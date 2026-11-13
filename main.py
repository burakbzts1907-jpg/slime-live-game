import os
import asyncio
import json
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from TikTokLive import TikTokLiveClient
from TikTokLive.events import ConnectEvent, LikeEvent, GiftEvent

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

clients = set()
USERNAME = os.getenv("TIKTOK_USERNAME", "user27612891182928372810")
tiktok = TikTokLiveClient(unique_id=USERNAME)

async def broadcast(data):
    for ws in list(clients):
        try:
            await ws.send_text(json.dumps(data))
        except:
            clients.remove(ws)

@tiktok.on(ConnectEvent)
async def on_connect(event):
    await broadcast({"type": "log", "message": f"Bağlandı: @{event.unique_id}"})

@tiktok.on(LikeEvent)
async def on_like(event):
    await broadcast({"type": "like", "message": f"{event.user.nickname} beğendi!"})

@tiktok.on(GiftEvent)
async def on_gift(event):
    await broadcast({"type": "gift", "message": f"{event.user.nickname} {event.gift.name} gönderdi!"})

@app.websocket("/ws")
async def ws_endpoint(websocket: WebSocket):
    await websocket.accept()
    clients.add(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            packet = json.loads(data)
            action = packet.get("action")
            await broadcast({"type": action, "message": f"Test: {action} eklendi!"})
    except WebSocketDisconnect:
        clients.remove(websocket)

@app.get("/")
async def root():
    return FileResponse("static/index.html")

@app.on_event("startup")
async def startup():
    asyncio.create_task(tiktok.connect())
