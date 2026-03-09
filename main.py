import os, uvicorn
from fastapi import FastAPI, WebSocket
from fastapi.responses import HTMLResponse

app = FastAPI()

# INTERFAZ ULTRA-MINIMALISTA PARA LIMPIAR MEMORIA
html = """
<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"></head>
<body style="text-align:center; padding-top:50px; font-family:sans-serif;">
    <h2 style="color:#FF4081">♻️ RESET DE SERVIDOR</h2>
    <input id="i" placeholder="Escribe algo..." style="padding:10px; border-radius:5px;">
    <button onclick="s()" style="padding:10px 20px; background:#FF4081; color:white; border:none; border-radius:5px;">TEST</button>
    <div id="m" style="margin-top:20px; color:#555;"></div>
    <script>
        let ws = new WebSocket((location.protocol==='https:'?'wss:':'ws:')+"//"+location.host+"/ws");
        ws.onmessage = (e) => { document.getElementById('m').innerHTML += "<div>"+e.data+"</div>"; };
        function s() { let v = document.getElementById('i'); if(v.value) { ws.send(v.value); v.value=''; } }
    </script>
</body>
</html>
"""

@app.get("/")
async def get(): return HTMLResponse(html)

@app.websocket("/ws")
async def ws(w: WebSocket):
    await w.accept()
    try:
        while True:
            d = await w.receive_text()
            await w.send_text(f"RECIBIDO: {d}") # ECO DIRECTO
    except: pass

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
