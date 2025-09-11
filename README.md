# 🎙️ Real-Time Accent Reduction for Voice Transcription  

A production-ready solution for real-time speech-to-text with accent normalization, built with **WebRTC + Django ASGI + faster-whisper (CTranslate2)**.  
This project is designed to improve transcription accuracy for global English accents while maintaining ultra-low latency for live calls.

## 🚀 Features  

- **Real-Time Streaming ASR** – Uses [faster-whisper](https://github.com/guillaumekln/faster-whisper) for high-speed transcription with CTranslate2 backend.  
- **Accent Normalization Layer** – Phoneme-aware correction using G2P + confusion maps + domain-specific lexicon.  
- **WebRTC Integration** – Browser client captures audio via `getUserMedia`, streams over SRTP, and displays transcripts live.  
- **Low Latency (<300 ms)** – Optimized with VAD, sliding windows, and partial hypothesis updates.  
- **Scalable Deployment** – Containerized with Docker & docker-compose; deployable on AWS ECS/EKS.  
- **Monitoring Ready** – Exposes Prometheus metrics & Grafana dashboards for latency, WER, and throughput.  

---

## 🏗️ Architecture Overview  

```mermaid
flowchart TD
    A[Browser Client (React)] -->|WebRTC Audio| B[Django ASGI + Channels]
    B -->|PCM Frames via WS| C[Inference ASGI Service]
    C -->|VAD + Streaming ASR| D[faster-whisper (CT2)]
    D -->|Transcript Output| E[Accent Normalization Layer]
    E -->|Corrected Transcript| A
    B -->|Metrics| F[Prometheus + Grafana]
````

---

## 🛠️ Tech Stack

| Layer                | Tools / Frameworks                        | Purpose                          |
| ---------------------| ----------------------------------------- | -------------------------------- |
| Backend              | Django (ASGI), Django Channels, FastAPI   | REST APIs, WebSocket signaling   |
| Real-Time Media      | aiortc, WebRTC, coturn                    | Audio streaming, NAT traversal   |
| ASR Engine           | faster-whisper (CTranslate2), Silero-VAD  | Streaming transcription + VAD    |
| Accent Normalization | G2P, KenLM/Transformer LM, Confusion Maps | Post-editing & lexicon biasing   |
| Frontend             | React, WebRTC getUserMedia API            | Mic capture + live transcript UI |
| Containerization     | Docker, docker-compose                    | Environment consistency          |
| Monitoring           | Prometheus, Grafana, Sentry               | Metrics, dashboards, alerting    |
| Deployment           | AWS ECS/EKS, NGINX, Gunicorn/Uvicorn      | Scalable production setup        |
| Testing              | Locust, pytest, A/B Testing               | Load testing & regression        |
| Data & Storage       | S3, Redis, PostgreSQL                     | Model artifacts, cache, sessions |

---

## 📂 Repository Structure

```plaintext
accent-reduction/
├─ services/
│  ├─ api-django/           # Django ASGI API + Channels
│  └─ inference-asgi/       # VAD, ASR, post-editor service
├─ web/
│  └─ client/               # React + WebRTC client
├─ ops/
│  ├─ docker/               # Dockerfiles & docker-compose
│  ├─ monitoring/           # Prometheus rules, Grafana dashboards
│  └─ k8s/                  # (Optional) Kubernetes manifests
├─ data/
│  ├─ lexicons/             # Domain-specific wordlists
│  └─ eval/                 # Evaluation datasets
├─ docs/                    # Architecture diagrams & API specs
└─ tests/                   # Unit & integration tests
```

---

## ⚙️ Setup & Run

### 1️⃣ Clone the Repository

```bash
git clone https://github.com/<your-username>/accent-reduction.git
cd accent-reduction
```

### 2️⃣ Create & Activate Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
```

### 3️⃣ Run Services with Docker

```bash
docker-compose up --build
```

### 4️⃣ Open Client UI

Visit `http://localhost:3000` in your browser → Click "Start Mic" → See live transcripts.

---

## 📊 Metrics & Monitoring

* **Prometheus**: `http://localhost:9090`
* **Grafana**: `http://localhost:3001` (preconfigured dashboards available under `ops/monitoring`)

---

## 🧪 Testing

Run unit tests and load tests locally:

```bash
pytest tests/
locust -f tests/load_test.py
```

---

## 📌 Roadmap

* [ ] Improve phoneme mapping coverage for more accents
* [ ] Train lightweight seq2seq post-editor for further error reduction
* [ ] Add speaker diarization for multi-speaker conversations
* [ ] Mobile SDK with on-device ASR support

---

## 🤝 Contributions

Contributions, bug reports, and feature requests are welcome!
Feel free to open an **issue** or submit a **pull request**.

---

## 📜 License

--

```