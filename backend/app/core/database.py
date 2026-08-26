
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings

# 1. DECLARA Base aquí y usa en TODOS los modelos
Base = declarative_base()

# 2. Crea engine y SessionLocal igual
engine = create_engine(settings.database_url, echo=True, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
