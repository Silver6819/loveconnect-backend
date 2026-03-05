# --- CONFIGURACIÓN REFORZADA ---
DATABASE_URL = os.environ.get("DATABASE_URL")

if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

database = databases.Database(DATABASE_URL)
metadata = sqlalchemy.MetaData()

usuarios_db = sqlalchemy.Table(
    "usuarios_loveconnect",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column("nombre", sqlalchemy.String, unique=True),
    sqlalchemy.Column("edad", sqlalchemy.Integer),
    sqlalchemy.Column("ubicacion", sqlalchemy.String),
    sqlalchemy.Column("foto_b64", sqlalchemy.Text),
    sqlalchemy.Column("ultima_conexion", sqlalchemy.String),
    sqlalchemy.Column("es_premium", sqlalchemy.Boolean, default=False)
)

# Esto CREA la tabla si no existe físicamente en Railway
engine = sqlalchemy.create_engine(DATABASE_URL)
metadata.create_all(engine) 

app = FastAPI()
