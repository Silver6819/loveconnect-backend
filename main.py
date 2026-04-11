# -------------------------
# 🔔 NOTIFICACIONES GLOBALES
# -------------------------
@app.get("/notificaciones")
async def notificaciones(request: Request):
    try:
        usuario_actual = request.session.get("usuario")

        if not usuario_actual or usuario_actual == "Invitado":
            return {"nuevos": []}

        nuevos = []

        if engine:
            with engine.connect() as conn:

                result = conn.execute(text("""
                    SELECT emisor, mensaje FROM mensajes
                    WHERE receptor = :usuario
                    ORDER BY id DESC
                    LIMIT 5
                """), {"usuario": usuario_actual})

                nuevos = [
                    {"emisor": row[0], "mensaje": row[1]}
                    for row in result.fetchall()
                ]

        return {"nuevos": nuevos}

    except:
        return {"nuevos": []}
