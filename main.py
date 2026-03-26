from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import os

app = FastAPI()

base_dir = os.path.dirname(os.path.realpath(__file__))
templates = Jinja2Templates(directory=os.path.join(base_dir, "templates"))

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/registro", response_class=HTMLResponse)
async def registro(request: Request, nombre: str = Form(...), email: str = Form(...)):
    return templates.TemplateResponse("index.html", {
        "request": request,
        "mensaje": f"¡Hola {nombre}! Registro exitoso 💘"
    })
