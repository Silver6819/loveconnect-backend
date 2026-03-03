import os
import stripe
import base64
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from openai import OpenAI
from dotenv import load_dotenv

# Carga las llaves de seguridad de forma privada
load_dotenv()

app = FastAPI()

# --- CONFIGURACIÓN DE CLIENTES (PROTEGIDOS CON OS.GETENV) ---
# Estos comandos buscan tus llaves reales en la configuración del servidor
client_ai = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

@app.get("/api/health")
async def health():
    return {"status": "ok", "message": "LoveConnect Server Activo"}

# --- 1. VERIFICACIÓN FACIAL CON IA (CORREGIDO LÍNEAS 21-25) ---
@app.post("/api/verify-face")
async def verify_face(image_b64: str):
    try:
        # Formato correcto para que GPT-4o procese la imagen sin errores
        response = client_ai.chat.completions.create(
            model="gpt-4o",
            messages=
            }]
        )
        
        # Extraemos la respuesta (SI/NO)
        contenido = response.choices.message.content.upper()
        verificado = "SI" in contenido
        
        return {"verified": verificado, "status": "success"}
    
    except Exception as e:
        print(f"Error en IA: {e}")
        raise HTTPException(status_code=500, detail="Error en el motor de verificación facial")

# --- 2. PASARELA DE PAGOS REAL CON STRIPE ($2.00 USD) ---
@app.post("/api/checkout/emojis")
async def create_checkout(user_id: str):
    try:
        # Creamos el cobro de 2 dólares (200 centavos)
        intent = stripe.PaymentIntent.create(
            amount=200, 
            currency="usd",
            metadata={
                "user_id": user_id,
                "product": "emoji_pack_premium"
            }
        )
        # Enviamos la confirmación a la App
        return {"clientSecret": intent.client_secret}
        
    except Exception as e:
        print(f"Error en Stripe: {e}")
        raise HTTPException(status_code=400, detail=str(e))

# --- 3. GESTIÓN DE CHAT Y MENSAJES ---
@app.post("/api/chat/send")
async def send_message(sender_id: str, receiver_id: str, text: str):
    # Aquí el servidor procesa el envío de mensajes gratuitos
    return {"status": "sent", "message": text}
