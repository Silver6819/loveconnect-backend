import os
import base64
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from openai import OpenAI
from dotenv import load_dotenv

# Carga las llaves de seguridad de forma privada
load_dotenv()

app = FastAPI()

# --- CONFIGURACIÓN DE CLIENTES (SIN STRIPE PARA EL SALVADOR) ---
client_ai = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@app.get("/api/health")
async def health():
    return {"status": "ok", "message": "LoveConnect Server Activo en El Salvador"}

# --- 1. VERIFICACIÓN FACIAL CON IA ---
@app.post("/api/verify-face")
async def verify_face(image_b64: str):
    try:
        response = client_ai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Is there a real human face in this image? Answer only YES or NO."},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"}}
                    ]
                }
            ]
        )
        
        contenido = response.choices[0].message.content.upper()
        verificado = "YES" in contenido or "SI" in contenido
        
        return {"verified": verificado, "status": "success"}
    
    except Exception as e:
        print(f"Error en IA: {e}")
        raise HTTPException(status_code=500, detail="Error en el motor de verificación facial")

# --- 2. SIMULADOR DE PAGOS (BYPASS) ---
@app.post("/api/checkout/emojis")
async def create_checkout(user_id: str):
    # Simulamos el éxito para que la App avance sin pedir la llave de Stripe
    try:
        return {
            "clientSecret": "pay_simulated_success_sv",
            "status": "success",
            "message": "Simulación activa para El Salvador"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail="Error en el simulador")

# --- 3. GESTIÓN DE CHAT ---
@app.post("/api/chat/send")
async def send_message(sender_id: str, receiver_id: str, text: str):
    return {"status": "sent", "message": text}        
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
