import logging
import numpy as np
import torch
from aiortc import RTCPeerConnection, RTCSessionDescription
from aiortc.contrib.media import MediaBlackhole
from fastapi import FastAPI, WebSocket
from faster_whisper import WhisperModel
import silero_vad
from silero_vad.utils_vad import get_speech_timestamps, collect_chunks

logger = logging.getLogger("asgi-inference")
logging.basicConfig(level=logging.INFO)

app = FastAPI()

# =========================
# Load models once at startup
# =========================
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
logger.info(f"Loading Faster-Whisper on {DEVICE}...")

whisper_model = WhisperModel("small", device=DEVICE, compute_type="float16" if DEVICE == "cuda" else "int8")
vad_model = silero_vad.get_speech_model("cuda" if DEVICE == "cuda" else "cpu")

# =========================
# Constants
# =========================
VAD_SAMPLING_RATE = 16000
SAMPLES_PER_FRAME = int(0.02 * VAD_SAMPLING_RATE)  # 20ms frame = 320 samples


class Session:
    """Hold per-connection state (buffers, counters, websocket)"""
    def __init__(self, ws: WebSocket):
        self.ws = ws
        self.speech_buffer = []
        self.segment = []
        self.speech_active = False
        self.last_emit_samples = 0

    async def send_json(self, payload):
        await self.ws.send_json(payload)


class TranscribingAudioSink:
    """AudioSink that handles buffering, VAD, ASR"""

    def __init__(self, session: Session):
        self.session = session

    async def _process_chunk(self, pcm16_chunk: np.ndarray):
        """
        Process each incoming PCM16 chunk:
        - Normalize
        - Push to buffer
        - Run VAD every ~200ms
        - Emit partial or final transcripts
        """
        # Normalize to float32 in [-1,1]
        pcm_float = (pcm16_chunk.astype(np.float32) / 32768.0)

        # Accumulate raw PCM16 in buffer
        self.session.speech_buffer.append(pcm16_chunk)

        # Check if enough audio (~200ms) is accumulated
        buf = np.concatenate(self.session.speech_buffer, axis=0)
        if len(buf) >= SAMPLES_PER_FRAME * 10:
            self.session.speech_buffer.clear()

            buf_float = buf.astype(np.float32) / 32768.0
            ts = get_speech_timestamps(buf_float, vad_model, sampling_rate=VAD_SAMPLING_RATE)

            if ts:
                # Collect voiced regions
                speech = collect_chunks(ts, buf_float)
                self.session.segment.append((speech * 32768.0).astype(np.int16))
                self.session.speech_active = True
            else:
                # If we were in speech and now silence -> finalize
                if self.session.speech_active and self.session.segment:
                    final = np.concatenate(self.session.segment)
                    await asr_and_emit(final, self.session, is_final=True)
                    # reset
                    self.session.speech_active = False
                    self.session.segment = []

        # Emit partial every ~1s during active speech
        if self.session.speech_active and self.session.segment:
            total_len = sum(len(s) for s in self.session.segment)
            if total_len - self.session.last_emit_samples > VAD_SAMPLING_RATE:  # ~1s
                partial = np.concatenate(self.session.segment)
                await asr_and_emit(partial, self.session, is_final=False)
                self.session.last_emit_samples = total_len


async def asr_and_emit(pcm16: np.ndarray, session: Session, is_final: bool):
    """Run Faster-Whisper on PCM16 and emit transcript"""
    audio = pcm16.astype(np.float32) / 32768.0

    segments, info = whisper_model.transcribe(
        audio=audio,
        language="en",
        vad_filter=False,
        word_timestamps=False,
        beam_size=1,
        condition_on_previous_text=False,
        temperature=0.0,
    )

    text = "".join(s.text for s in segments)
    payload = {
        "type": "transcript",
        "final": is_final,
        "text": text.strip(),
        "info": {"duration_s": len(pcm16) / VAD_SAMPLING_RATE},
    }
    await session.send_json(payload)
    logger.info("%s transcript: %s", "FINAL" if is_final else "PARTIAL", payload["text"])


# =========================
# FastAPI WebSocket endpoint
# =========================
@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    session = Session(ws)
    sink = TranscribingAudioSink(session)

    try:
        while True:
            msg = await ws.receive_bytes()
            pcm16_chunk = np.frombuffer(msg, dtype=np.int16)
            await sink._process_chunk(pcm16_chunk)
    except Exception as e:
        logger.error("WebSocket error: %s", e)
    finally:
        await ws.close()
