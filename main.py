import os
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import uvicorn

app = FastAPI()

@app.get("/")
async def root():
    # Una página simple para confirmar que LoveConnect está vivo
    html_content = """
    <html>
        <head><title>LoveConnect - Reset</title></head>
        <body style="font-family: sans-serif; text-align: center; padding-top: 50px;">
            <h1 style="color: #e91e63;">¡Sistema LoveConnect Activo!</h1>
            <p>La limpieza fue exitosa. Render está funcionando correctamente.</p>
            <p>Estamos listos para volver a intentar la conexión con el elefante.</p>
        </body>
    </html>
    """
    return HTMLResponse(content=html_content)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
