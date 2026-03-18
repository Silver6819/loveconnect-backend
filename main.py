from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from datetime import date
import uvicorn

app = FastAPI()

# --- BASE DE DATOS DE ALMAS (Simulada) ---
# Aquí controlamos quién es Premium y quién está en el Chat de Castigo
usuarios_db = {
    "Silver676": {
        "pass": "admin123", 
        "lvl": "∞", 
        "rango": "Creador", 
        "prestigio": 9999,
        "tipo": "Premium",
        "castigado": False
    },
    "UsuarioEjemplo": {
        "pass": "123",
        "lvl": "1",
        "rango": "Explorador",
        "prestigio": 0,
        "tipo": "Básico",
        "castigado": False
    }
}

# --- LÓGICA DE NEGOCIO ---
def calcular_edad(fecha_nacimiento: str):
    try:
        today = date.today()
        birth = date.fromisoformat(fecha_nacimiento)
        return today.year - birth.year - ((today.month, today.day) < (birth.month, birth.day))
    except:
        return 0

# --- DISEÑO UNIFICADO (HTML + CSS CYBER-NEON) ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>LoveConnect v6.0 - Edición Estelar</title>
    <style>
        body { background:#050505; color:white; font-family:Arial, sans-serif; margin:0; overflow-x:hidden; }
        :root { --blue:#00f7ff; --pink:#ff00c8; }
        .neon-blue { color:var(--blue); text-shadow:0 0 10px var(--blue); }
        .neon-pink { color:var(--pink); text-shadow:0 0 10px var(--pink); }
        
        /* Pantalla +18 */
        #age-gate { position:fixed; top:0; left:0; width:100%; height:100%; background:black; 
                    display:flex; flex-direction:column; justify-content:center; align-items:center; z-index:1000; text-align:center; }
        
        /* Contenedores y Cards */
        .container { max-width:450px; margin:40px auto; padding:20px; border: 1px solid #222; border-radius:15px; background:#0a0a0a; text-align:center; }
        input { background:black; border:2px solid var(--blue); padding:10px; color:white; margin:10px 0; width:80%; outline:none; border-radius:5px; }
        
        button { background:transparent; border:2px solid var(--blue); color:var(--blue); padding:12px 25px; cursor:pointer; transition:0.3s; font-weight:bold; text-transform:uppercase; }
        button:hover { box-shadow:0 0 15px var(--blue); background:var(--blue); color:black; }
        
        .pink-btn { border-color:var(--pink); color:var(--pink); }
        .pink-btn:hover { box-shadow:0 0 20px var(--pink); background:var(--pink); color:white; }

        .memberships { display:flex; gap:10px; justify-content:center; margin:25px 0; }
        .card { border:2px solid; padding:15px; width:180px; border-radius:12px; background:#0f0f0f; transition: 0.3s; }
        .blue-card { border-color:var(--blue); box-shadow:0 0 10px var(--blue); }
        .pink-card { border-color:var(--pink); box-shadow:0 0 15px var(--pink); }
        
        /* Perfil */
        .profile-img { width:110px; height:110px; border-radius:50%; border:3px solid var(--blue); box-shadow:0 0 15px var(--blue); margin-bottom:10px; }
        .action-btn { cursor:pointer; font-size:1.3rem; transition:0.3s; margin: 0 8px; }
        .action-btn:hover { transform: scale(1.3); filter: drop-shadow(0 0 5px white); }
        
        #chat-box { text-align:left; height:250px; overflow-y:auto; background:#000; padding:15px; border:1px solid #111; margin-top:20px; border-radius:10px; }
    </style>
</head>
<body>

    <div id="age-gate">
        <h1 class="neon-pink">ADVERTENCIA +18</h1>
        <p style="max-width:350px; line-height:1.5;">Esta es una comunidad para adultos. Cualquier falta a las reglas te enviará directamente al <b>Chat de Castigo</b>.</p>
        <button onclick="document.getElementById('age-gate').style.display='none'">ACEPTAR Y CONTINUAR</button>
    </div>

    <div class="container">
        <h1 class="neon-blue" style="letter-spacing:3px;">LOVE CONNECT</h1>
        
        <div class="profile">
            <img src="https://api.dicebear.com/7.x/bottts/svg?seed=Silver" class="profile-img">
            <h2 class="neon-blue">LvL: {{ lvl }}</h2>
            <p style="color:#888;">Rango: <span class="neon-pink">{{ rango }}</span></p>
        </div>

        <hr style="border:0.5px solid #222; margin:20px 0;">

        <div class="memberships">
            <div class="card blue-card">
                <h3 class="neon-blue">Básico</h3>
                <p style="font-size:0.85rem;">Chat, Audio y Galería<br><b>¡ILIMITADOS!</b></p>
                <button style="font-size:0.65rem;">TU NIVEL</button>
            </div>
            
            <div class="card pink-card">
                <h3 class="neon-pink">Premium</h3>
                <p style="font-size:0.85rem;">Todo lo Básico +<br><b>Videos Ilimitados</b></p>
                <a href="https://www.paypal.me/silver676" target="_blank" style="text-decoration:none;">
                    <button class="pink-btn" style="font-size:0.65rem;">PODER CÓSMICO</button>
                </a>
            </div>
        </div>

        <div id="registro" style="margin-top:20px;">
            <h4 class="neon-blue">Registro de Almas</h4>
            <input type="date" id="birthdate" onchange="actualizarEdad()">
            <input type="text" id="age_display" placeholder="Edad Calculada" readonly>
        </div>

        <div id="chat-box">
            <p><span class="neon-blue"><b>Admin:</b></span> Bienvenidos a la Red Estelar. ❤️ 🔗</p>
            <p><b>Usuario_Beta:</b> ¿Alguien para compartir videos? <span class="action-btn">❤️</span></p>
        </div>
    </div>

    <script>
        function actualizarEdad() {
            let fecha = new Date(document.getElementById("birthdate").value);
            let hoy = new Date();
            let edad = hoy.getFullYear() - fecha.getFullYear();
            if (hoy.getMonth() < fecha.getMonth() || (hoy.getMonth() == fecha.getMonth() && hoy.getDate() < fecha.getDate())) {
                edad--;
            }
            document.getElementById("age_display").value = edad + " años reales";
        }
    </script>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
async def home():
    # Simulamos que eres tú el que entra
    user = usuarios_db["Silver676"]
    
    # Verificamos si está castigado
    if user["castigado"]:
        return "<h1>HAS SIDO ENVIADO AL CHAT DE CASTIGO</h1>"
    
    return HTML_TEMPLATE.replace("{{ lvl }}", str(user["lvl"])).replace("{{ rango }}", user["rango"])

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=10000)
