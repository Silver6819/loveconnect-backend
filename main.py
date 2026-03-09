import os, uvicorn
from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse

app = FastAPI()

# Configuración de Silver Breaker
ADMIN = "Silver Breaker"
PAYPAL = "https://www.paypal.com/paypalme/silver676"
OBRA = "https://books2read.com/u/mYG1X0"

# Memoria de mensajes (se limpia si el servidor se reinicia)
chat_log = []

@app.get("/")
async def home():
    # Construimos las burbujas de mensaje
    mensajes_html = "".join([
        f'<div style="background:#f1f1f1; padding:10px; margin-bottom:10px; border-radius:15px; font-size:14px; max-width:85%; border:1px solid #eee;">{m}</div>' 
        for m in chat_log
    ])
    
    return HTMLResponse(f"""
    <!DOCTYPE html>
    <html style="height:100%;">
    <head>
        <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=0">
        <style>
            * {{ box-sizing: border-box; }}
            body {{ margin: 0; background: #fff5f7; font-family: sans-serif; height: 100vh; display: flex; flex-direction: column; }}
            .h {{ background: #FF4081; color: white; padding: 15px; text-align: center; font-weight: bold; flex-shrink: 0; }}
            #c {{ flex: 1; overflow-y: auto; background: white; padding: 15px; }}
            .u {{ padding: 10px; background: white; border-top: 1px solid #eee; display: flex; gap: 8px; flex-shrink: 0; }}
            input {{ flex: 1; padding: 12px; border: 2px solid #f8bbd0; border-radius: 25px; outline: none; font-size: 16px; }}
            button {{ background: #FF4081; color: white; border: none; border-radius: 20px; padding: 0 20px; font-weight: bold; cursor: pointer; box-shadow: 0 4px #c2185b; }}
            button:active {{ box-shadow: none; transform: translateY(4px); }}
            .n {{ display: flex; justify-content: space-around; background: white; padding: 10px; border-top: 1px solid #eee; }}
            .b {{ border: none; background: none; color: #FF4081; font-weight: bold; font-size: 11px; text-decoration: none; }}
        </style>
    </head>
    <body>
        <div class="h">💖 LoveConnect</div>
        <div id="c">{mensajes_html if mensajes_html else '<p style="color:gray;text-align:center;">No hay mensajes aún...</p>'}</div>
        <form action="/enviar" method="post" class="u">
            <input name="msg" placeholder="Escribe aquí..." autocomplete="off" required>
            <button type="submit">ENVIAR</button>
        </form>
        <div class="n">
            <a class="b" href="{OBRA}" target="_blank">📖 MI OBRA</a>
            <a class="b" href="{PAYPAL}" target="_blank">💳 PAYPAL</a>
            <a class="b" href="/">🔄 RECARGAR</a>
        </div>
        <script>window.onload = () => {{ let c = document.getElementById('c'); c.scrollTop = c.scrollHeight; }};</script>
    </body>
    </html>
    """)

@app.post("/enviar")
async def enviar_msg(msg: str = Form(...)):
    # Guardamos el mensaje (limitado a los últimos 20 para no saturar)
    chat_log.append(f"<b>{ADMIN}:</b> {msg}")
    if len(chat_log) > 20: chat_log.pop(0)
    # Redirigimos al inicio para ver el mensaje nuevo
    return HTMLResponse("<script>location.href='/'</script>")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
