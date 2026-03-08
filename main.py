import os, uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse

app = FastAPI()
ADMIN = "Silver Breaker"
PAYPAL = "https://www.paypal.com/paypalme/silver676"
OBRA = "https://books2read.com/u/mYG1X0"

html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=0">
    <style>
        * {{ box-sizing: border-box; }}
        body {{ margin: 0; background: #fff5f7; font-family: sans-serif; height: 100vh; display: flex; flex-direction: column; overflow: hidden; }}
        .h {{ background: #FF4081; color: white; height: 50px; line-height: 50px; text-align: center; font-weight: bold; flex-shrink: 0; }}
        #c {{ flex: 1; overflow-y: auto; background: white; padding: 10px; }}
        .m {{ background: #f1f1f1; padding: 10px; border-radius: 12px; margin-bottom: 8px; max-width: 85%; font-size: 14px; width: fit-content; }}
        .u {{ padding: 10px; background: white; border-top: 1px solid #eee; display: flex; gap: 8px; flex-shrink: 0; align-items: center; }}
        input {{ flex: 1; padding: 12px; border: 1px solid #ddd; border-radius: 25px; outline: none; font-size: 16px; }}
        .s {{ border: none; background: #FF4081; color: white; border-radius: 50%; width: 45px; height: 45px; cursor: pointer; font-size: 20px; }}
        .f {{ display: flex; justify-content: space-around; padding: 10px; background: white; border-top: 1px solid #eee; flex-shrink: 0; }}
        .b {{ border: none; background: none; color: #FF4081; font-weight: bold; font-size: 12px; }}
        #l {{ position: fixed; inset: 0; background: #fff5f7; display: flex; flex-direction: column; justify-content: center; align-items: center; z-index: 100; }}
    </style>
</head>
<body>
    <div id="l">
        <h2 style="color:#FF4081">💖 LoveConnect</h2>
        <input type="text" id="user" placeholder="Tu Nombre" style="max-width:200px; margin-bottom:15px; border-radius:10px; padding:10px; border:1px solid #ddd;">
        <button onclick="st()" style="background:#FF4081; color:white; border:none; padding:12px 40px; border-radius:25px; font-weight:bold;">ENTRAR</button>
    </div>
    <div class="h">💖 LoveConnect</div>
    <div id="c"></div>
    <div class="u">
        <input type="text" id="msg" placeholder="Escribe..." onkeypress="if(event.key==='Enter') sd()">
        <button class="s" onclick="sd()">🚀</button>
    </div>
    <div class="f">
        <button class="b" onclick="alert('Lee mi obra: {OBRA}')">📅 MI OBRA</button>
        <button class="b" onclick="window.open('{PAYPAL}')">💳 PAYPAL</button>
        <button class="b" onclick="location.reload()">👤 SALIR</button>
    </div>
    <script>
        let ws; let nick = "";
        const chat = document.getElementById('c');
        const inp = document.getElementById('msg');

        function st() {{
            nick = document.getElementById('user').value.trim() || "Usuario";
            document.getElementById('l').style.display = 'none';
            co();
        }}

        function co() {{
            const p = location.protocol === 'https:' ? 'wss:' : 'ws:';
            ws = new WebSocket(p + "//" + location.host + "/ws/" + encodeURIComponent(nick));
            ws.onmessage = (e) => {{
                if(e.data === "CLR") chat.innerHTML = "";
                else {{
                    const d = document.createElement('div'); d.className='m'; d.textContent=e.data;
                    chat.appendChild(d); chat.scrollTop = chat.scrollHeight;
                }}
            }};
            ws.onclose = () => setTimeout(co, 1000);
        }}

        function sd() {{
            const val = inp.value.trim();
            if(!val) return;
            if(ws && ws.readyState === 1) {{
                ws.send(val);
                inp.value = "";
            }} else {{
                co(); // Reconecta si se perdió el hilo
                setTimeout(() => {{ if(ws.readyState===1) {{ ws.send(val); inp.value=""; }} }}, 500);
            }}
        }}
    </script>
</body>
</html>
"""

class Manager:
    def __init__(self): self.a = {}
    async def con(self, u, w): await w.accept(); self.a[u] = w
    def disc(self, u):
        if u in self.a: del self.a[u]
    async def b(self, m):
        for w in list(self.a.values()):
            try: await w.send_text(m)
            except: pass

man = Manager()
@app.get("/")
async def get(): return HTMLResponse(html)

@app.websocket("/ws/{{u}}")
async def ws(websocket: WebSocket, u: str):
    await man.con(u, websocket)
    try:
        while True:
            data = await websocket.receive_text()
            if data == "/limpiar" and u == ADMIN: await man.b("CLR")
            else: await man.b(f"{{'⭐ [ADMIN]' if u==ADMIN else u}}: {{data}}")
    except: man.disc(u)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
