import os
import uvicorn
from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI()

# "Base de datos" temporal para usuarios
usuarios = {}

@app.get("/", response_class=HTMLResponse)
async def inicio():
    return """
    <html>
        <head>
            <title>LoveConnect - Dating App</title>
            <style>
                body { font-family: sans-serif; text-align: center; background: #fff0f3; padding: 40px; }
                .card { background: white; padding: 30px; border-radius: 20px; box-shadow: 0 10px 25px rgba(255,75,110,0.2); max-width: 450px; margin: auto; }
                h1 { color: #ff4b6e; }
                .btn { display: block; width: 100%; padding: 12px; margin: 10px 0; background: #ff4b6e; color: white; text-decoration: none; border-radius: 8px; font-weight: bold; }
                .user-box { border: 1px solid #eee; padding: 10px; margin-top: 10px; border-radius: 8px; text-align: left; }
            </style>
        </head>
        <body>
            <div class="card">
                <h1>💖 LoveConnect</h1>
                <p>Encuentra personas cerca de ti</p>
                <hr>
                <a href="/api/usuarios/ver" class="btn">👥 Ver Personas Registradas</a>
                <p style="font-size: 0.8em;">Usa las rutas para registrarte y chatear</p>
            </div>
        </body>
    </html>
    """

# --- REGISTRO Y UBICACIÓN ---
@app.get("/api/registrar/{nombre}/{edad}/{ubicacion}")
async def registrar(nombre: str, edad: int, ubicacion: str):
    usuarios[nombre] = {
        "edad": edad,
        "ubicacion": ubicacion,
        "chats": []
    }
    return {"mensaje": f"Bienvenido/a {nombre}", "perfil": usuarios[nombre]}

# --- VER TODOS LOS PERFILES ---
@app.get("/api/usuarios/ver")
async def ver_usuarios():
    return {"comunidad": usuarios}

# --- CHATS DE CONVERSACIÓN ---
@app.get("/api/chatear/{emisor}/{receptor}/{mensaje}")
async def enviar_mensaje(emisor: str, receptor: str, mensaje: str):
    if receptor in usuarios:
        registro_mensaje = f"{emisor} dice: {mensaje}"
        usuarios[receptor]["chats"].append(registro_mensaje)
        return {"estado": "Mensaje enviado", "conversacion": usuarios[receptor]["chats"]}
    return {"error": "El usuario receptor no existe"}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
