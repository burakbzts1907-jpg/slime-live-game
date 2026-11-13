import os
import asyncio
import json
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from TikTokLive import TikTokLiveClient
from TikTokLive.events import ConnectEvent, DisconnectEvent, GiftEvent

app = FastAPI()
clients = set()

USERNAME = os.getenv("TIKTOK_USERNAME", "user27612891182928372810")
tiktok = TikTokLiveClient(unique_id=USERNAME)

async def broadcast(data):
    dead = []
    for ws in clients:
        try:
            await ws.send_text(json.dumps(data))
        except Exception:
            dead.append(ws)
    for ws in dead:
        clients.discard(ws)

@tiktok.on(ConnectEvent)
async def connected(event):
    await broadcast({"type": "status", "message": "TikTok bağlandı!"})

@tiktok.on(DisconnectEvent)
async def disconnected(event):
    await broadcast({"type": "status", "message": "TikTok bağlantısı kesildi"})

@tiktok.on(GiftEvent)
async def gift(event):
    if getattr(event, "repeat_end", True) is False:
        return

    await broadcast({
        "type": "gift",
        "gift": str(event.gift.name),
        "user": str(event.user.nickname),
        "count": int(getattr(event, "repeat_count", 1))
    })

@app.on_event("startup")
async def startup():
    asyncio.create_task(tiktok.start())

@app.get("/")
async def home():
    return {"message": "Slime LIVE oyunu çalışıyor"}

@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    clients.add(ws)
    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        clients.discard(ws)

app.mount("/static", StaticFiles(directory="static"), name="static")
