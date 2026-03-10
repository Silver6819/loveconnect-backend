import os, uvicorn
from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from starlette.middleware.sessions import SessionMiddleware

app = FastAPI()
# Llave de seguridad para las sesiones
app.add_middleware(SessionMiddleware, secret_key="silver-secret-key")

ADMIN_NAME = "Silver Breaker"
PAYPAL_URL = "https://www.paypal.com/paypalme/silver676"
OBRA_URL = "https://books2read.com/u/mYG1X0"

chat_log = []

@app.get("/")
async def home(request: Request):
    user = request.session.get("user")
    
    if not user:
        return HTMLResponse(f"""
        <html>
        <head>
            <title>Bienvenido</title>
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                @keyframes fadeIn {{ from {{ opacity:0; transform:translateY(-10px); }} to {{ opacity:1; transform:translateY(0); }} }}
                body {{ margin:0; font-family: sans-serif; background:#fff0f6; display:flex; justify-content:center; align-items: flex-start; height:100vh; pt: 50px; }}
                .login-container {{ 
                    background:white; padding:40px; border-radius:30px; 
                    box-shadow:0 10px 25px rgba(0,0,0,0.05); text-align:center; 
                    width:85%; max-width:320px; animation: fadeIn 0.8s ease-out;
                    margin-top: 60px; /* Subimos la caja para el teclado */
                }}
                .logo {{ font-size:26px; font-weight:bold; color:#ff4fa3; margin-bottom:25px; }}
                .name-input {{ width:100%; padding:15px; border:1px solid #eee; border-radius:15px; outline:none; margin-bottom:20px; font-size:16px; box-sizing:border-box; }}
                .enter-btn {{ background:#ff4fa3; color:white; border:none; padding:15px; width:100%; border-radius:15px; font-weight:bold; cursor:pointer; transition:0.2s; }}
                .enter-btn:active {{ transform: scale(0.95); }}
            </style>
        </head>
        <body>
            <div class="login-container">
                <div class="logo">💗 LoveConnect</div>
                <form action="/login" method="post" onsubmit="saveName()">
                    <input type="text" id="user-input" name="username" placeholder="Tu nombre" class="name-input" required autocomplete="off">
                    <button type="submit" class="enter-btn">Entrar al Chat</button>
                </form>
            </div>
            <script>
                // Propuesta de ChatGPT: Cargar nombre guardado
                window.onload = function() {{
                    const saved = localStorage.getItem("chat_name");
                    if (saved) document.getElementById("user-input").value = saved;
                }};
                // Guardar nombre al entrar
                function saveName() {{
                    const name = document.getElementById("user-input").value;
                    localStorage.setItem("chat_name", name);
                }}
            </script>
        </body>
        </html>
        """)

    # Renderizado del Chat
    mensajes_html = "".join([
        f'<div class="bubble"><b>{m["user"]} {"🌟" if m["user"] == ADMIN_NAME else ""}:</b> {m["text"]}</div>' 
        for m in chat_log
    ])

    admin_tools = f'<form action="/clear" method="post" style="text-align:center;"><button class="clear-btn">🗑 Limpiar Chat</button></form>' if user == ADMIN_NAME else ""

    return HTMLResponse(f"""
    <html>
    <head>
        <title>LoveConnect Chat</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {{ margin:0; font-family: sans-serif; background:#fff0f6; display:flex; justify-content:center; }}
            .container {{ width:100%; max-width:420px; height:100vh; display:flex; flex-direction:column; background:white; }}
            header {{ background:linear-gradient(135deg,#ff4fa3,#ff7ac6); color:white; text-align:center; padding:15px; font-weight:bold; position:relative; }}
            .logout {{ position:absolute; right:15px; top:12px; color:white; text-decoration:none; font-size:22px; }}
            #chat-box {{ flex:1; overflow-y:auto; padding:15px; display:flex; flex-direction:column; }}
            .bubble {{ background:linear-gradient(135deg,#ff4fa3,#ff7ac6); color:white; padding:10px 14px; border-radius:18px; margin-bottom:10px; max-width:85%; font-size:14px; box-shadow:0 2px 5px rgba(0,0,0,0.05); }}
            .clear-btn {{ background:#444; color:white; border:none; padding:8px 16px; border-radius:12px; margin: 10px auto; cursor:pointer; font-size:12px; }}
            .send-form {{ display:flex; border-top:1px solid #eee; padding: 10px; background:white; }}
            input {{ flex:1; border:1px solid #eee; padding:12px; border-radius: 20px; outline:none; }}
            .btn-send {{ background:#ff4fa3; border:none; color:white; padding:10px 15px; border-radius: 20px; margin-left:5px; font-weight:bold; }}
            button:active {{ transform: scale(0.95); }}
            footer {{ text-align:center; padding:10px; font-size:12px; background:#fafafa; border-top:1px solid #eee; }}
            footer a {{ color:#ff4fa3; text-decoration:none; font-weight:bold; }}
        </style>
    </head>
    <body>
        <div class="container">
            <header>💖 LoveConnect <a href="/logout" class="logout">⎋</a></header>
            <div id="chat-box">
                {mensajes_html if mensajes_html else '<div style="text-align:center;color:gray;margin-top:20px;font-style:italic;">🔒 Canal Seguro Activo</div>'}
                <div id="anchor"></div>
            </div>
            {admin_tools}
            <form action="/send" method="post" class="send-form">
                <input id="msg-input" name="msg" placeholder="Escribe un mensaje..." required autocomplete="off">
                <button type="submit" class="btn-send">Enviar</button>
            </form>
            <footer><a href="{OBRA_URL}" target="_blank">📖 MI OBRA</a> | <a href="{PAYPAL_URL}" target="_blank">💳 PAYPAL</a></footer>
        </div>
        <script>
            window.onload = function() {{
                const cb = document.getElementById("chat-box");
                cb.scrollTop = cb.scrollHeight;
                document.getElementById("msg-input").focus();
            }};
        </script>
    </body>
    </html>
    """)

@app.post("/login")
async def login(request: Request, username: str = Form(...)):
    request.session["user"] = username
    return RedirectResponse(url="/", status_code=303)

@app.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/")

@app.post("/send")
async def send(request: Request, msg: str = Form(...)):
    user = request.session.get("user", "Anónimo")
    chat_log.append({"user": user, "text": msg})
    if len(chat_log) > 30: chat_log.pop(0)
    return RedirectResponse(url="/", status_code=303)

@app.post("/clear")
async def clear_chat():
    global chat_log
    chat_log = []
    return RedirectResponse(url="/", status_code=303)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
