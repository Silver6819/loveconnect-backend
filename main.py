import os
from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse
import sqlalchemy

# Configuración de Base de Datos Ultra-Ligera (SQLite)
DB_URL = "sqlite:///./love.db"
engine = sqlalchemy.create_engine(DB_URL, connect_args={"check_same_thread": False})
metadata = sqlalchemy.MetaData()

# Tabla de mensajes
msg_t = sqlalchemy.Table(
    "m", metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column("u", sqlalchemy.String(50)),
    sqlalchemy.Column("t", sqlalchemy.String(500))
)
metadata.create_all(engine)

app = FastAPI()

@app.get("/", response_class=HTMLResponse)
async def home():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>LoveConnect</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body { font-family: sans-serif; background: #f0f2f5; margin: 0; padding: 20px; }
            .modal { 
                display: flex; position: fixed; top: 0; left: 0; width: 100%; height: 100%; 
                background: rgba(255, 255, 255, 0.1); 
                backdrop-filter: blur(15px); /* Efecto Blur Moderno */
                -webkit-backdrop-filter: blur(15px);
                z-index: 1000; justify-content: center; align-items: center; 
            }
            .modal-content { 
                background: white; padding: 25px; border-radius: 15px; 
                box-shadow: 0 10px 25px rgba(0,0,0,0.1); max-width: 80%; text-align: center; 
            }
            button { background: #0084ff; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer; }
        </style>
    </head>
    <body>
        <div id="rulesModal" class="modal">
            <div class="modal-content">
                <h2>Reglas de LoveConnect</h2>
                <p>1. Respeta a los demás.<br>2. Diviértete escribiendo.</p>
                <button onclick="document.getElementById('rulesModal').style.display='none'">Aceptar</button>
            </div>
        </div>
        <h1>Bienvenido a LoveConnect</h1>
        <p>El servidor está activo y listo.</p>
    </body>
    </html>
    """
