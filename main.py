import os, uvicorn
from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse

app = FastAPI()
# Esta lista guardará los mensajes para confirmar que el servidor responde
memoria_purgada = ["SISTEMA RESETEADO"]

@app.get("/")
async def index():
    # Diseño ultra-simple para no saturar el navegador
    return HTMLResponse(f"""
    <html>
    <head><meta name="viewport" content="width=device-width, initial-scale=1.0"></head>
    <body style="text-align:center; font-family:sans-serif; background:#fff5f7; padding-top:50px;">
        <h2 style="color:#FF4081">🚿 CRASH DE PURGA</h2>
        <div style="background:white; padding:20px; border-radius:10px; display:inline-block; border:2px solid #FF4081;">
            <p>Último mensaje: <b style="color:blue;">{memoria_purgada[-1]}</b></p>
            <form action="/purgar" method="post">
                <input name="texto" placeholder="Escribe para limpiar..." style="padding:10px;" required>
                <br><br>
                <button type="submit" style="background:#FF4081; color:white; border:none; padding:10px 20px; border-radius:5px; font-weight:bold;">FORZAR ENVÍO</button>
            </form>
        </div>
        <br><br>
        <p style="font-size:12px; color:gray;">Si el mensaje de arriba cambia, el servidor se destrabó.</p>
    </body>
    </html>
    """)

@app.post("/purgar")
async def purgar(texto: str = Form(...)):
    # Esto sobreescribe la memoria del servidor a la fuerza
    memoria_purgada.append(texto)
    # Evitamos que la lista crezca demasiado
    if len(memoria_purgada) > 5: memoria_purgada.pop(0)
    # Recargamos la página principal
    return HTMLResponse("<script>location.href='/'</script>")

if __name__ == "__main__":
    puerto = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=puerto)
