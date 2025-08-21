import uvicorn
from fastapi import FastAPI, WebSocket

app = FastAPI()

@app.websocket("/ws/echo")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    while True:
        data = await ws.receive_text()
        await ws.send_text(f"echo: {data}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8500)
