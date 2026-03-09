import os, uvicorn
from fastapi import FastAPI, WebSocket
from fastapi.responses import HTMLResponse

app = FastAPI()

html = """
<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"></head>
<body style="text-align:center; padding-top:50px; font-family:sans-serif; background:#f0f0f0;">
    <h2 style="color:#FF4081">🚿 LIMPIEZA DE TUBO</h2>
    <input id="i" placeholder="Escribe..." style="padding:10px; width:70%;">
    <br><br>
    <button onclick="s()" style="padding:15px 30px; background:#FF4081; color:white; border:none; border-radius:5px; font-weight:bold;">ENVIAR TEST</button>
    <div id="m" style="margin-top:20px; font-weight:bold; color:blue;"></div>
    <script>
        // Forzamos la conexión limpia
        let ws = new WebSocket((location.protocol==='https:'?'wss:':'ws:')+"//"+location.host+"/chat");
        ws.onmessage = (e) => { 
            document.getElementById('m').innerHTML = "RESPUESTA: " + e.data; 
        };
        function s() { 
            let v = document.getElementById('i'); 
            if(v.value && ws.readyState === 1) { 
                ws.send(v.value); 
                v.value=''; 
            } else {
                alert("Conexión no lista. Reintentando...");
                location.reload();
            }
        }
    </script>
</body>
</html>
"""

@app.get("/")
async def get(): return HTMLResponse(html)

@app.websocket("/chat")
async def chat_socket(w: WebSocket):
    await w.accept()
    try:
        while True:
            d = await w.receive_text()
            # Respondemos de inmediato para confirmar el camino
            await w.send_text(f"OK -> {d}")
    except: pass

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
