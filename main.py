import os, uvicorn
from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse

app = FastAPI()

# --- DATOS DE SILVER BREAKER ---
ADMIN_NAME = "Silver Breaker"
PAYPAL_URL = "https://www.paypal.com/paypalme/silver676"
OBRA_URL = "https://books2read.com/u/mYG1X0"

# Memoria temporal de mensajes
chat_log = []

@app.get("/")
async def home():
    # Construcción de las burbujas con el diseño de ChatGPT
    mensajes_html = "".join([
        f'<div class="bubble"><b>{ADMIN_NAME} 🌟:</b> {m}</div>' 
        for m in chat_log
    ])

    return HTMLResponse(f"""
    <html>
    <head>
        <title>LoveConnect</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {{
                margin:0;
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
                background:#fff0f6;
                display:flex;
                justify-content:center;
            }}
            .container {{
                width:100%;
                max-width:420px;
                height:100vh;
                display:flex;
                flex-direction:column;
                background:white;
                box-shadow:0 0 15px rgba(0,0,0,0.08);
            }}
            header {{
                background:linear-gradient(135deg,#ff4fa3,#ff7ac6);
                color:white;
                text-align:center;
                padding:15px;
                font-weight:bold;
                font-size:18px;
            }}
            #chat-box {{
                flex:1;
                overflow-y:auto;
                padding:20px;
            }}
            .bubble {{
                background:linear-gradient(135deg,#ff4fa3,#ff7ac6);
                color:white;
                padding:10px 14px;
                border-radius:18px;
                margin-bottom:10px;
                max-width:85%;
                font-size:14px;
                box-shadow:0 3px 8px rgba(0,0,0,0.08);
                word-wrap: break-word;
            }}
            form {{
                display:flex;
                border-top:1px solid #eee;
            }}
            input {{
                flex:1;
                border:none;
                padding:14px;
                font-size:16px;
                outline:none;
            }}
            button {{
                background:#ff4fa3;
                border:none;
                color:white;
                padding:0 20px;
                cursor:pointer;
                font-weight:bold;
            }}
            footer {{
                text-align:center;
                padding:12px;
                font-size:12px;
                background:#fafafa;
                border-top: 1px solid #eee;
            }}
            footer a {{
                color:#ff4fa3;
                text-decoration:none;
                font-weight:bold;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <header>💖 LoveConnect</header>
            <div id="chat-box">
                {mensajes_html if mensajes_html else '<p style="text-align:center; color:gray;">No hay mensajes aún...</p>'}
            </div>
            <form action="/send" method="post">
                <input name="msg" placeholder="Escribe algo..." required autocomplete="off">
                <button type="submit">Enviar</button>
            </form>
            <footer>
                <a href="{OBRA_URL}" target="_blank">📖 MI OBRA</a> | 
                <a href="{PAYPAL_URL}" target="_blank">💳 PAYPAL</a>
            </footer>
        </div>
        <script>
            let chat = document.getElementById("chat-box");
            chat.scrollTop = chat.scrollHeight;
        </script>
    </body>
    </html>
    """)

@app.post("/send")
async def send(msg: str = Form(...)):
    # Guardamos el mensaje
    chat_log.append(msg)
    # Mantener solo los últimos 20 para no saturar
    if len(chat_log) > 20: chat_log.pop(0)
    # Redirigir al inicio para ver el cambio
    return HTMLResponse("<script>location.href='/'</script>")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
