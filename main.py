import sqlalchemy
# ... (tus otras importaciones)

# Función para limpiar mensajes antiguos y evitar saturación
async def limpiar_datos_antiguos():
    query = mensajes_comunidad.delete() # Borra todo para empezar de cero
    await database.execute(query)
    print("Base de datos optimizada y limpia.")
