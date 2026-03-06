@app.on_event("startup")
async def startup():
    if not database.is_connected: await database.connect()
    # ESTO LIMPIA TODO PARA EVITAR EL CRASH
    try:
        await database.execute("DROP TABLE IF EXISTS usuarios_loveconnect CASCADE")
        await database.execute("DROP TABLE IF EXISTS usuarios_v2 CASCADE")
        await database.execute("DROP TABLE IF EXISTS encuestas CASCADE")
        
        # Crear tablas desde cero
        metadata.create_all(sqlalchemy.create_engine(DATABASE_URL.replace("postgresql://", "postgresql+psycopg2://")))
    except:
        pass
