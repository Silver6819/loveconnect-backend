import os
from typing import List
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
import sqlalchemy

# --- CONFIGURACIÓN DE BASE DE DATOS LIGERA ---
DB_URL = "sqlite:///./love.db"
engine = sqlalchemy.create_engine(DB_URL, connect_args={"check_same_thread": False})
metadata = sqlalchemy.MetaData()
msg_t = sqlalchemy.Table(
    "m", metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column("u", sqlalchemy.String(50)),
    sqlalchemy.Column("t", sqlalchemy.String(500))
)
metadata.create_all(engine)

app = FastAPI()

# --- LÓGICA DE LA SALA DE CASTIGO ---
PALABRAS_PROHIBIDAS = ["insulto1", "ofensa2", "spam", "toxicidad"] 

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()

@app.get("/", response_class=HTMLResponse)
async def get():
    return """
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>LoveConnect</title>
        <style>
            body { font-family: 'Segoe UI', sans-serif; background: #f0f2f5; margin: 0; height: 100vh; overflow: hidden; }
            #main-chat { display: flex; flex-direction: column; height: 100vh; width: 100%; opacity: 0; pointer-events: none; transition: opacity 0.5s; }
            .chat-header { background: white; padding: 15px; text-align: center; font-weight: bold; color: #FF4081; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
            #messages { flex: 1; overflow-y: auto; padding: 20px; display: flex; flex-direction: column; gap: 10px; }
            .msg { background: white; padding: 10px 15px; border-radius: 18px; max-width: 80%; align-self: flex-start; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
            .system-msg { background: #ffe4e1; color: #d81b60; align-self: center; font-size: 13px; border: 1px solid #ffcdd2; padding: 5px 15px; border-radius: 10px; }
            .input-box { padding: 15px; background: white; display: flex; gap: 10px; border-top: 1px solid #eee; }
            .input-style { flex: 1; border: 1px solid #ddd; padding: 12px 20px; border-radius: 25px; outline: none; }

            /* MODAL PREMIUM CON REGISTRO DE NOMBRE */
            .modal-overlay {
                position: fixed; top: 0; left: 0; width: 100%; height: 100%;
                background: rgba(255, 255, 255, 0.3); backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px);
                display: flex; justify-content: center; align-items: center; z-index: 2000;
            }
            .modal-box {
                background: white; padding: 30px; border-radius: 30px; box-shadow: 0 20px 40px rgba(0,0,0,0.1); width: 85%; max-width: 380px; text-align: center;
            }
            .modal-box h1 { color: #FF4081; font-size: 24px; margin-top: 0; }
            .modal-box ul { text-align: left; list-style: none; padding: 0 20px; color: #444; margin: 15px 0; font-size: 15px; }
            .name-input { width: 80%; padding: 12px; margin: 15px 0; border: 1px solid #FF4081; border-radius: 12px; outline: none; text-align: center; font-size: 16px; }
            .btn-enter { background: #FF4081; color: white; border: none; width: 100%; padding: 16px; border-radius: 15px; font-weight: bold; cursor: pointer; font-size: 18px; }
        </style>
    </head>
    <body>
        <div id="rulesModal" class="modal-overlay">
            <div class="modal-box">
                <h1>📜 Reglas LoveConnect</h1>
                <ul>
                    <li>✅ Solo para mayores de 18 años.</li>
                    <li>✅ Respeto total (Sala de Castigo activa).</li>
                    <li>✅ Privacidad responsable.</li>
                </ul>
                <input type="text" id="
