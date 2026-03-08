import os, uvicorn
from fastapi import FastAPI, WebSocket
from fastapi.responses import HTMLResponse

app = FastAPI()
ADMIN = "Silver Breaker"
PAYPAL = "https://www.paypal.com/paypalme/silver676"
OBRA = "https://books2read.com/u/mYG1X0"

html = f"""
<!DOCTYPE html>
<html style="height:100%; overflow:hidden;">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <style>
        * {{ box-sizing: border-box; -webkit-tap-highlight-color: transparent; }}
        body {{ margin: 0; background: #fff5f7; font-family: sans-serif; height: 100%; display: flex; flex-direction: column; }}
        .h {{ background: #FF4081; color: white; padding: 15px; text-align: center; font-weight: bold; flex-shrink: 0; }}
        #c {{ flex: 1; overflow-y: auto; background: white; padding: 15px; }}
        .m {{ background: #f1f1f1; padding: 10px; border-radius: 15px; margin-bottom: 10px; max-width: 85%; font-size: 14px; width: fit-content; word-wrap: break-word; }}
        .u {{ padding: 10px; background: white; border-top: 1px solid #eee; display: flex; gap: 8px; flex-shrink: 0; align-items: center; }}
        input {{ flex: 1; padding: 12px; border: 1px solid #ddd; border-radius: 20px; outline: none; font-size: 16px; background: #fafafa; }}
        /* NUEVO BOTÓN REFORZADO */
        .s {{ 
            border: none; background: #FF4081; color: white; border-radius: 12px; 
            min-width: 60px; height: 45px; cursor: pointer; font-size: 18px; 
            font-weight: bold; display: flex; align-items: center; justify-content: center;
            box-shadow: 0 4px #c2185b; transition: 0.1s;
        }}
        .s:active {{ box-shadow: 0 0 #c2185b; transform: translateY(4px); }}
        
        .n {{ display: flex; justify-content: space-around; background: white; padding: 10px; border-top: 1px solid #eee; flex-shrink: 0; }}
        .b {{ border: none; background: none; color: #FF4081; font-weight: bold; font-size: 11px; }}
        #l {{ position: fixed; inset: 0; background: #fff5f7; display: flex; flex-direction: column; justify-content: center; align-items: center; z-index: 1000; }}
    </style>
</head>
<body>
    <div id="l">
        <h2 style="color:#FF4081">💖 LoveConnect</h2>
        <input type="text" id="un" placeholder="Tu Nombre" style="max-width:200px; margin-bottom:15px; border-radius:10px; padding:12px;">
        <button onclick="st()" style="background:#FF4081; color:white; border:none; padding:12px 40px; border-radius:25px; font-weight:bold;">ENTRAR</button>
    </div>
    <div class="h">💖 LoveConnect</div>
    <div id="c"></div>
    <div class="u">
        <input type="text" id="mi" placeholder="Escribe algo..." autocomplete="off">
        <button type="button" class="s" id="btn_send">ENVIAR</button>
    </div>
    <div class="n">
        <button class="b" onclick="alert('Obra: {OBRA}')">📅 MI OBRA</button>
        <button class="b" onclick="window.open('{PAYPAL}')">💳 PAYPAL</button>
        <button class="b" onclick="location.reload()">👤 SALIR</button>
    </div>
    <script>
        let ws; let nick = "";
        const chat = document.getElementById('c');
        const inp = document.getElementById('mi');
        const btn = document.getElementById('btn_send');

        function st() {{
            nick = document.getElementById('un').value.trim() || "Usuario";
            document.getElementById('l').style.display = 'none';
            co();
        }}
        function co() {{
            const p = location.protocol === 'https:' ? 'wss:' : 'ws:';
            ws = new WebSocket(p + "//" + location.host + "/ws/" + encodeURIComponent(nick));
            ws.onmessage = (e) => {{
                let d = document.createElement('div'); d.className = 'm'; d.textContent = e.data;
                chat.appendChild(d); chat.scrollTop = chat.scrollHeight;
            }};
            ws.onclose = () => setTimeout(co, 1500);
        }}
        
        // FUNCIÓN DE ENVÍO REFORZADA
        function sd() {{
            const texto = inp.value.trim();
            if(texto && ws && ws.readyState === 1) {{
                ws.send(texto);
                inp.value = "";
                inp.focus();
            }}
        }}

        // Escuchar tanto el clic como el Enter
        btn.onclick = sd;
        inp.onkeypress = (e) => {{ if(e.key === "Enter") sd(); }};
    </script>
</body>
</html>
"""

@app.get("/")
async def get(): return HTMLResponse(html)

@app.websocket("/ws/{{u}}")
async def ws(websocket: WebSocket, u: str):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            tag = "⭐ [ADMIN]" if u == ADMIN else u
            await websocket.send_text(f"{{tag}}: {{data}}")
    except: pass

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
