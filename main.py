from fastapi import FastAPI
app = FastAPI()
@app.get("/")
def r(): return "SISTEMA RESETEADO"
