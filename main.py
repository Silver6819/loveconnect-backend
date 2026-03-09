import os, uvicorn
from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse

app = FastAPI()

# --- DATOS DE SILVER BREAKER ---
ADMIN_NAME = "Silver Breaker"
PAYPAL_URL = "https://www.paypal.com/paypalme/silver676"
OBRA_URL = "https://books2read.com/u/mYG1X0"

chat_log = []

# DISEÑO SEPARADO PARA EVITAR CRASH
CSS_STYLE = """
body { margin:0; font-family: sans-serif; background:#fff0f6; display:flex; justify-content:center; }
.container { width:100%; max-width:420px; height:100vh; display:flex; flex-direction:column; background:white; }
header { background:linear-gradient(135deg,#ff4fa3,#ff7ac6); color:white; text-align:center; padding:15px; font-weight:bold; }
#chat-box { flex:1; overflow-y:auto; padding:20px; display: flex; flex-direction: column; }
.bubble { background:linear-gradient(135deg,#ff4fa3,#ff7ac6); color:white; padding:10px 14px; border-radius:18px; margin-bottom:10px; max-width:85%; font-size:14px; word-wrap: break-word; }
form { display:flex; border-top:1px solid #eee; padding: 10px; }
input { flex:1; border:1px solid #eee; padding:12px; border-radius: 20px; outline:none; }
button { background:#ff4fa3; border:none; color:white; padding:10px 20px; border-radius: 20px; margin-left: 10px; font-weight:bold; }
footer { text-align:center; padding:15px; font-size:12px; background:#fafafa; }
footer a { color:#ff4fa3; text-decoration:none; font-weight:bold; }
"""

@app.get("/")
async def home():
    mensajes_html = "".join([f'<div class="bubble"><b>{ADMIN_NAME} 🌟:</b> {m}</div>' for m in chat_log])
    
    html_content = f"""
    <html>
    <head>
        <title>LoveConnect</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>{CSS_STYLE}</style>
    </head>
    <body>
        <div class="container">
            <header>💖 LoveConnect</header>
            <div id="chat-box">{mensajes_html if mensajes_html else '<p style="text-align:center;color:gray;">¡Servidor Listo!</p>'}</div>
            <form action="/send" method="post">
                <input name="msg" placeholder="Escribe un mensaje..." required autocomplete="off">
                <button type="submit">Enviar</button>
            </form>
            <footer>
                <a href="{OBRA_URL}" target="_blank">📖 OBRA</a> | 
                <a href="{PAYPAL_URL}" target="_blank">💳 PAYPAL</a>
            </footer>
        </div>
        <script>
            var objDiv = document.getElementById("chat-box");
            objDiv.scrollTop = objDiv.scrollHeight;
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.post("/send")
async def send(msg: str = Form(...)):
    chat_log.append(msg)
    if len(chat_log) > 20: chat_log.pop(0)
    return HTMLResponse("<script>location.href='/'</script>")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
