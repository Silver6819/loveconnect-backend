import os
import base64
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

@app.get("/api/health")
async def health():
    return {"status": "ok", "message": "LoveConnect Activo"}

@app.post("/api/verify-face")
async def verify_face(image_b64: str):
    return {"verified": True, "status": "success"}

@app.post("/api/checkout/emojis")
async def create_checkout(user_id: str):
    return {"clientSecret": "simulado", "status": "success"}

@app.post("/api/chat/send")
async def send_message(sender_id: str, receiver_id: str, text: str):
    return {"status": "sent", "message":
