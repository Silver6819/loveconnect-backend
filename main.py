import os, uvicorn
from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse

app = FastAPI()
# Almacén de mensajes en memoria volátil
mensajes = ["⭐ SISTEMA REINICIADO"]

@app.get("/")
async def home():
    # Generamos la lista de mensajes para mostrar
    chat_html = "".join([f'<div style="background:#f1f1f1;padding:10px;margin-bottom:8px;border-radius:10px;">{m}</div>' for m in mensajes])
    
    return HTMLResponse(f"""
    <html>
    <head><meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=0">
    <style>
        body {{ font-family: sans-serif; margin:0; background:#fff5f7; display:flex; flex-direction:column; height:100vh; }}
        .h {{ background:#FF4081; color:white; padding:15px; text-align:center; font-weight:bold; }}
        #c {{ flex:1; overflow-y:auto; padding:15px; background:white; }}
        .u {{ padding:10px; background:white; border-top:1px solid #eee; display:flex; gap:5px; }}
        input {{ flex:1; padding:12px; border:1px solid #ddd; border-radius:20px; outline:none; font-size:16px; }}
        button {{ background:#FF4081; color:white; border:none; border-radius:15px; padding:0 20px; font-weight:bold; cursor:pointer; box-shadow:0 3px #c2185b; }}
    </style>
    </head>
    <body>
        <div class="h">💖 LoveConnect (Vía Directa)</div>
        <div id="c">{chat_html}</div>
        <form action="/send" method="post" class="u">
            <input name="m" placeholder="Escribe un mensaje..." autocomplete="off" required>
            <button type="submit">ENVIAR</button>
        </form>
        <script>document.getElementById('c').scrollTop = document.getElementById('c').scrollHeight;</script>
    </body>
    </html>
    """)

@app.post("/send")
async def send(m: str = Form(...)):
    # Guardamos el mensaje y recargamos
    mensajes.append(f"Usuario: {m}")
    if len(mensajes) > 20: mensajes.pop(0)
    return HTMLResponse("<script>location.href='/'</script>")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
