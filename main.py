# ... (Importaciones y DB se mantienen igual) ...

ESTILOS = """
<style>
    body { font-family: 'Segoe UI', sans-serif; background: #fdf2f4; margin: 0; padding: 10px; text-align: center; }
    .card { background: white; border-radius: 20px; padding: 15px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); margin-bottom: 20px; position: relative; border: 1px solid #ffeef2; }
    
    /* BOTÓN DIAMANTE ANIMADO */
    .btn-tienda { background: gold; border: none; padding: 12px; border-radius: 50%; cursor: pointer; font-size: 1.5em; box-shadow: 0 4px 10px rgba(0,0,0,0.2); animation: pulse 2s infinite; }
    @keyframes pulse { 0% { transform: scale(1); } 50% { transform: scale(1.1); } 100% { transform: scale(1); } }

    /* VENTANA PREMIUM MEJORADA */
    .modal-pago { display: none; position: fixed; top: 10%; left: 5%; width: 90%; background: white; border-radius: 25px; padding: 25px; box-shadow: 0 10px 50px rgba(0,0,0,0.4); z-index: 1000; border: 3px solid gold; box-sizing: border-box; }
    .btn-pay { background: #0070ba; color: white; padding: 18px; border-radius: 15px; text-decoration: none; display: block; margin: 12px 0; font-weight: bold; font-size: 1.2em; }
    .btn-chivo { background: #161616; color: #00ffcc; padding: 18px; border-radius: 15px; text-decoration: none; display: block; margin: 12px 0; font-weight: bold; border: 2px solid #00ffcc; font-size: 1.2em; }
    
    /* BOTÓN CERRAR (MÁS GRANDE) */
    .btn-cerrar-modal { background: #ff4b6e; color: white; border: none; padding: 15px 40px; border-radius: 12px; cursor: pointer; margin-top: 20px; font-weight: bold; width: 100%; font-size: 1.1em; }

    /* LIKES DE DIAMANTE */
    .diamond-btn { background: #f0f7ff; border: 2px solid #2196f3; color: #2196f3; padding: 10px 20px; border-radius: 30px; cursor: pointer; font-weight: bold; font-size: 1em; }
</style>
"""

@app.get("/", response_class=HTMLResponse)
async def inicio():
    return f"""
    <html>
        <head><meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1">{ESTILOS}</head>
        <body>
            <div style="display:flex; justify-content: space-between; align-items: center; padding: 10px;">
                <h1 style="color:#ff4b6e; margin:0; font-size: 1.5em;">💖 LoveConnect</h1>
                <button onclick="abrirTienda()" class="btn-tienda">💎</button>
            </div>

            <div id="tienda" class="modal-pago">
                <h2 style="margin-top:0; color:#333;">👑 ¡Sé un Miembro VIP!</h2>
                <p style="color:#555; font-size: 1.1em;">Acceso ilimitado y <b>3 Diamantes Especiales</b> para tus perfiles favoritos de la semana.</p>
                
                <a href="https://www.paypal.me/TU_USUARIO" target="_blank" class="btn-pay">Pagar con PayPal</a>
                <a href="https://chivowallet.com" target="_blank" class="btn-chivo">Pagar con Chivo Wallet</a>
                
                <button onclick="cerrarTienda()" class="btn-cerrar-modal">Cerrar Ventana</button>
            </div>

            <div class="card">
                <h3 style="margin-top:0;">Crear perfil</h3>
                <input type="text" id="n" placeholder="Nombre completo">
                <input type="text" id="u" placeholder="Zacatecoluca, La Paz">
                <textarea id="q" placeholder="¿Quién eres y qué buscas?"></textarea>
                <button class="btn" onclick="enviar()" style="background:#ff4b6e; color:white; border:none; padding:15px; border-radius:12px; width:100%; font-weight:bold; font-size: 1.1em;">Publicar Mi Perfil</button>
            </div>
            
            <a href="/api/usuarios/ver" style="color:#ff4b6e; font-weight:bold; text-decoration:none; display:block; margin-top:10px;">Ver Comunidad 🌍</a>

            <script>
                function abrirTienda() {{ document.getElementById('tienda').style.display = "block"; }}
                function cerrarTienda() {{ document.getElementById('tienda').style.display = "none"; }}
            </script>
        </body>
    </html>
    """
