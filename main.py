import os, uvicorn
from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse

app = FastAPI()

ADMIN_NAME = "Silver Breaker"
PAYPAL_URL = "https://www.paypal.com/paypalme/silver676"
OBRA_URL = "https://books2read.com/u/mYG1X0"

chat_log = []

@app.get("/")
async def home():
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
            body {{ margin:0; font-family: -apple-system, sans-serif; background:#fff0f6; display:flex; justify-content:center; }}
            .container {{ width:100%; max-width:420px; height:100vh; display:flex; flex-direction:column; background:white; position:relative; }}
            
            header {{ background:linear-gradient(135deg,#ff4fa3,#ff7ac6); color:white; text-align:center; padding:15px; font-weight:bold; position:relative; }}
            .logout {{ position:absolute; right:15px; top:12px; color:white; text-decoration:none; font-size:22px; }}
            
            #chat-box {{ flex:1; overflow-y:auto; padding:15px; display:flex; flex-direction:column; justify-content:flex-start; }}
            
            .bubble {{ background:linear-gradient(135deg,#ff4fa3,#ff7ac6); color:white; padding:10px 14px; border-radius:18px; margin-bottom:10px; max-width:85%; font-size:14px; box-shadow:0 3px 8px rgba(0,0,0,0.05); }}

            .punish-room {{ background:#2b2b2b; color:#bbb; border-radius:20px; padding:12px; margin:10px 0; font-style:italic; text-align:center; font-size:13px; }}
            
            /* Mejoras de ChatGPT integradas */
            .clear-btn {{ background:#444; color:white; border:none; padding:8px 16px; border-radius:12px; margin: 20px auto; display: block; cursor:pointer; font-size:13px; transition: 0.2s; }}
            button:active {{ transform: scale(0.95); }}
            
            form.send-form {{ display:flex; border-top:1px solid #eee; padding: 10px; background:white; }}
            input {{ flex:1; border:1px solid #eee; padding:12px; border-radius: 20px; outline:none; }}
            .btn-send {{ background:#ff4fa3; border:none; color:white; padding:10px 15px; border-radius: 20px; margin-left:5px; font-weight:bold; cursor:pointer; }}
            
            footer {{ text-align:center; padding:10px; font-size:12px; background:#fafafa; border-top:1px solid #eee; }}
            footer a {{ color:#ff4fa3; text-decoration:none; font-weight:bold; }}
        </style>
    </head>
    <body>
        <div class="container">
            <header>💖 LoveConnect <a href="{OBRA_URL}" class="logout">⎋</a></header>
            <div id="chat-box">
                {mensajes_html if mensajes_html else '<div class="punish-room">🛡️ Sistema de Seguridad Activo</div>'}
            </div>
            <form action="/clear" method="post" style="margin:0;"><button class="clear-btn">🗑 Limpiar Chat</button></form>
            <form action="/send" method="post" class="send-form">
                <input name="msg" placeholder="Escribe un mensaje..." required autocomplete="off">
                <button type="submit" class="btn-send">Enviar</button>
            </form>
            <footer><a href="{OBRA_URL}" target="_blank">📖 MI OBRA</a> | <a href="{PAYPAL_URL}" target="_blank">💳 PAYPAL</a></footer>
        </div>
    </body>
    </html>
    """)

@app.post("/send")
async def send(msg: str = Form(...)):
    chat_log.append(msg)
    if len(chat_log) > 20: chat_log.pop(0)
    return HTMLResponse("<script>location.href='/'</script>")

@app.post("/clear")
async def clear_chat():
    global chat_log
    chat_log = []
    return HTMLResponse("<script>location.href='/'</script>")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
