import os
import traceback
from datetime import datetime
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import create_engine, text
from starlette.middleware.sessions import SessionMiddleware

app = FastAPI()

# 🔥 IMPORT NUEVO
from fastapi import Body

# (todo tu código queda EXACTAMENTE igual arriba)

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


# -------------------------
# 💰 PAYPAL IPN AUTOMÁTICO
# -------------------------
@app.post("/paypal_ipn")
async def paypal_ipn(request: Request):
    try:
        form = await request.form()

        # 🔥 Datos que manda PayPal
        payment_status = form.get("payment_status")
        usuario = form.get("custom")  # viene del botón
        receiver_email = form.get("receiver_email")

        # 🔥 VALIDACIONES BÁSICAS
        if payment_status == "Completed" and usuario:

            if engine:
                with engine.connect() as conn:
                    conn.execute(text("""
                        UPDATE usuarios
                        SET premium = TRUE
                        WHERE nombre = :usuario
                    """), {"usuario": usuario})
                    conn.commit()

        return {"ok": True}

    except Exception as e:
        print("ERROR PAYPAL:", e)
        return {"ok": False}
