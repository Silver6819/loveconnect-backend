import os, uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse

app = FastAPI()
# --- DATOS DE SILVER BREAKER ---
ADMIN = "Silver Breaker"
PAYPAL = "https://www.paypal.com/paypalme/silver676"
OBRA = "¡Lee 'El Espectro Infernal' aquí: https://books2read.com/u/mYG1X0"

html = f"""
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>LoveConnect</title>
    <style>
        body {{ margin: 0; background: #fff5f7; font-family: sans-serif; height: 100vh; display: flex; flex-direction: column; overflow: hidden; }}
        .h {{ background: #FF4081; color: white; padding: 15px; text-align: center; font-weight: bold; }}
        #c {{ flex: 1; overflow-y: auto; padding: 15px; background: white; }}
        .m {{ background: #f1f1f1; padding: 10px; border-radius: 12px; margin-bottom: 8px; max-width: 85%; font-size: 14px; width: fit-content; }}
        .u {{ padding: 10px; background: white; border-top: 1px solid #eee; display: flex; gap: 10px; align-items: center; justify-content: center; }}
        input {{ flex: 1; padding: 12px; border: 1px solid #ddd; border-radius: 25px; outline: none; }}
        .s {{ border: none; background: #FF4081; color: white; border-radius: 50%; width: 45px; height: 45px; cursor: pointer; font-size: 20px; }}
        .nav {{ display: flex; justify-content: space-around; background: white; padding: 10px; border-top: 1px solid #eee; }}
        .btn {{ border: none; background: none; color: #FF4081; font-weight: bold; cursor: pointer; font-size: 12px; }}
        #l {{ position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: #fff5f7; display: flex; flex-direction: column; justify-content: center; align-items: center; z-index: 100; }}
    </style>
</head>
<body>
    <div id="l">
        <h2 style="color:#FF4081">💖 LoveConnect</h2>
        <input type="text" id="user" placeholder="Tu Nombre" style="max-width:200px; margin-bottom:15px;">
        <button onclick="in()" style="background:#FF4081; color:white; border:none; padding:12px 30px; border-radius:20px;">ENTRAR</button>
    </div>
    <div class="h">💖 LoveConnect</div>
    <div id="c"></div>
    <div class="u">
        <input type="text" id="msg" placeholder="Hola a todos..." onkeypress="if(event.key==='Enter') sd()">
        <button class="s" onclick="sd()">🚀</button>
    </div>
    <div class="nav">
        <button class="btn" onclick="alert('{OBRA}')">📅 MI OBRA</button>
        <button class="btn" onclick="window.open('{PAYPAL}')">💳 PAYPAL</button>
        <button class="btn" onclick="location.reload()">👤 SALIR</button>
    </div>
    <script>
        let ws; let nick = "";
        function in() {{
            nick = document.getElementById('user').value.trim();
            if(!nick) return;
            document.getElementById('l').style.display = 'none';
            co();
        }}
        function co() {{
            ws = new WebSocket((location.protocol==='https:'?'wss:':'ws:')+"//"+location.host+"/ws/"+encodeURIComponent(nick));
            ws.onmessage = (e) => {{
                if(e.data === "CLR") {{ document.getElementById('c').innerHTML = ""; }}
                else {{ let d=document.createElement('div'); d.className='m'; d.textContent=e.data; let chat=document.getElementById('c'); chat.appendChild(d); chat.scrollTop=chat.scrollHeight; }}
            }};
            ws.onclose = () => setTimeout(co, 1000);
        }}
        function sd() {{
            let i = document.getElementById('msg');
            if(i.value && ws && ws.readyState === 1) {{ ws.send(i.value); i.value = ""; }}
            else if(i.value) {{ co(); setTimeout(() => {{ if(ws.readyState===1){{ ws.send(i.value); i.value=""; }} }}, 500); }}
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
    except WebSocketDisconnect: man.disc(u)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
