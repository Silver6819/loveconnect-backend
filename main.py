@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    usuarios = []

    if engine:
        try:
            with engine.connect() as conn:
                result = conn.execute(text("SELECT nombre FROM usuarios ORDER BY id DESC"))
                usuarios = [row[0] for row in result.fetchall()]
        except Exception as e:
            print("Error obteniendo usuarios:", e)

    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "mensaje": None,
            "usuarios": usuarios
        }
    )
