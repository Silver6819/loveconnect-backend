from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from datetime import date
import uvicorn

app = FastAPI()

# --- BASE DE DATOS DE ALMAS ---
usuarios_db = {
    "Silver676": {"pass": "1234", "lvl": "∞", "rango": "Creador", "tipo": "Premium", "castigado": False}
}

mensajes_globales = []
sugerencias = []

# --- TEMPLATE ÚNICO ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>LoveConnect v6.1</title>
    <style>
        body { background:#050505; color:white; font-family:Arial, sans-serif; margin:0; text-align:center; }
        :root { --blue:#00f7ff; --pink:#ff00c8; }
        .neon-blue { color:var(--blue); text-shadow:0 0 10px var(--blue); }
        .neon-pink { color:var(--pink); text-shadow:0 0 10px var(--pink); }
        
        #age-gate { position:fixed; top:0; left:0; width:100%; height:100%; background:black; 
                    display:flex; flex-direction:column; justify-content:center; align-items:center; z-index:2000; }
        
        .container { max-width:450px; margin:20px auto; padding:15px; border: 1px solid #222; border-radius:15px; background:#0a0a0a; }
        input { background:black; border:2px solid var(--blue); padding:10px; color:white; margin:5px 0; width:85%; outline:none; }
        
        button { background:transparent; border:2px solid var(--blue); color:var(--blue); padding:10px; cursor:pointer; font-weight:bold; width:90%; margin:10px 0; }
        button:hover { box-shadow:0 0 15px var(--blue); background:var(--blue); color:black; }
        
        .pink-btn { border-color:var(--pink); color:var(--pink); }
        .pink-btn:hover { box-shadow:0 0 15px var(--pink); background:var(--pink); color:white; }

        .card { border:1px solid; padding:10px; margin:10px; border-radius:10px; background:#111; display:inline-block; width:40%; vertical-align:top; font-size:0.7rem; }
        .blue-card { border-color:var(--blue); }
        .pink-card { border-color:var(--pink); }
        
        #chat-box { text-align:left; height:200px; overflow-y:auto; background:#000; padding:10px; border:1px solid #222; margin:10px 0; }
        .admin-link { color:red; font-size:0.7rem; text-decoration:none; display:block; margin-top:10px; }
    </style>
</head>
<body>

    <div id="age-gate">
        <h1 class="neon-pink">CONTENIDO +18</h1>
        <p style="padding:20px;">Si cometes faltas irás a la sala de castigo. ¿Aceptas continuar?</p>
        <button class="pink-btn" onclick="document.getElementById('age-gate').style.display='none'">ACEPTAR Y CONTINUAR</button>
    </div>

    <div class="container">
        <h2 class="neon-blue">LoveConnect</h2>
        <p><b>{{ user }}</b> <span class="neon-blue">[LvL: {{ lvl }}]</span></p>

        <div class="memberships">
            <div class="card blue-card">
                <h3 class="neon-blue">Básico</h3>
                <p>Chat, Audio y Galería<br><b>ILIMITADOS</b></p>
            </div>
            <div class="card pink-card">
                <h3 class="neon-pink">Premium</h3>
                <p>Todo +<br><b>Videos Ilimitados</b></p>
                <a href="https://www.paypal.me/silver676" target="_blank"><button class="pink-btn" style="width:100%; font-size:0.6rem;">MEJORAR</button></a>
            </div>
        </div>

        <div id="chat-box">
            {% for m in mensajes %}
                <p style="margin:5px 0;"><b>{{ m.user }}:</b> {{ m.msg }} <span>❤️ 🔗</span></p>
            {% endfor %}
        </div>

        <form action="/enviar" method="post">
            <input type="text" name="msg" placeholder="Escribe un mensaje..." required>
            <button type="submit">ENVIAR</button>
        </form>

        <form action="/sugerencia" method="post" style="margin-top:10px;">
            <input type="text" name="sug" placeholder="Sugerir mejora..." required>
            <button type="submit" style="width:40%; font-size:0.6rem;">Pedir</button>
        </form>

        {% if user == "Silver676" %}
            <a href="/borrar_todo" class="admin-link">[GOD MODE: BORRAR TODO EL CHAT]</a>
            <p style="font-size:0.6rem; color:gray;">Sugerencias recibidas: {{ total_sug }}</p>
        {% endif %}
    </div>

    <script>
        function actualizarEdad() {
            let birth = new Date(document.getElementById("birthdate").value);
            let age = new Date().getFullYear() - birth.getFullYear();
            document.getElementById("age_val").value = age + " años reales";
        }
    </script>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
async def home():
    # Simulamos que eres Silver676 entrando
    u = usuarios_db["Silver676"]
    html = HTML_TEMPLATE.replace("{{ user }}", "Silver676")
    html = html.replace("{{ lvl }}", u["lvl"])
    html = html.replace("{{ total_sug }}", str(len(sugerencias)))
    # Aquí renderizamos los mensajes (simplificado para el ejemplo)
    return html

@app.post("/enviar")
async def enviar(msg: str = Form(...)):
    mensajes_globales.append({"user": "Silver676", "msg": msg})
    return RedirectResponse("/", status_code=303)

@app.post("/sugerencia")
async def sugerir(sug: str = Form(...)):
    sugerencias.append(sug)
    return RedirectResponse("/", status_code=303)

@app.get("/borrar_todo")
async def borrar():
    mensajes_globales.clear()
    return RedirectResponse("/", status_code=303)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=10000)
