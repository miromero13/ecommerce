# Backend

API backend construida con FastAPI, SQLAlchemy y PostgreSQL.

## Requisitos

- Python 3.10+ recomendado
- PostgreSQL

## Instalación

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Variables de entorno

Crear un archivo `.env` en la raíz de `backend/` con este contenido:

```env
DATABASE_URL=postgresql+psycopg2://usuario:clave@localhost:5432/tu_db
SECRET_KEY=tu_clave_secreta
ACCESS_TOKEN_EXPIRE_MINUTES=60
ALGORITHM=HS256
```

## Ejecutar

```bash
uvicorn main:app --reload
```

La API quedará disponible normalmente en `http://127.0.0.1:8000`.

## Swagger / Docs

Sí, hay Swagger por defecto.

- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`

No hay configuración personalizada para desactivarlo en `main.py`.

## Cómo funciona

- `main.py` crea la app de FastAPI.
- Se cargan los routers de `auth`, `users` y `branches`.
- Las tablas se gestionan con Alembic.
- La autenticación usa JWT con Bearer token.
- Las contraseñas se guardan hasheadas con bcrypt.

## Rutas actuales

- `POST /api/auth/register`
- `POST /api/auth/login`
- `GET /api/users/`
- `PATCH /api/users/{id}/rol`
- `PATCH /api/users/{id}/branch`
- `GET /api/branches/`
- `POST /api/branches/`

## Migraciones y seeders

- Hay carpeta `alembic/` con una migración inicial.
- No encontré seeders ni fixtures.
- El esquema no se crea automáticamente al arrancar la app.

### Comandos de Alembic

```bash
alembic upgrade head
alembic revision -m "mensaje"
alembic downgrade -1
```

`alembic revision -m "mensaje"` crea un nuevo archivo de migración en `alembic/versions/` con ese mensaje como nombre descriptivo. No aplica cambios en la base de datos; solo genera la plantilla para que escribas los cambios.

`alembic downgrade -1` revierte la última migración aplicada. El `-1` significa "retrocede un paso".

Antes de levantar la API, ejecuta `alembic upgrade head` para crear o actualizar las tablas.

## Estructura

- `app/auth/` autenticación y JWT
- `app/core/` configuración, base de datos y errores
- `app/models/` modelos ORM
- `app/routes/` endpoints
- `app/schemas/` modelos Pydantic
- `app/services/` lógica de negocio
- `app/utils/` utilidades
