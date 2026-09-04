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
- `GET /api/providers/`
- `POST /api/providers/`
- `PATCH /api/providers/{id}/status`
- `GET /api/catalog/products`
- `GET /api/catalog/products/pending`
- `POST /api/catalog/products`
- `POST /api/catalog/products/provider-submission`
- `PATCH /api/catalog/products/{id}/status`
- `GET /api/catalog/availability`
- `GET /api/catalog/categories`, `/sizes`, `/colors`, `/seasons`, `/collections`

## Migraciones y seeders

- Hay carpeta `alembic/` con una migración inicial.
- No encontré seeders ni fixtures.
- El esquema no se crea automáticamente al arrancar la app.
- Seeder demo:

```bash
./.venv/bin/python -m alembic upgrade head
./.venv/bin/python seed.py
```

Contraseña de demo para todas las cuentas seed: `Fashion123!`

Nota: si `which alembic` apunta a `/opt/homebrew/bin/alembic`, usa `python -m alembic` para evitar el binario global roto. `python` sí puede salir del `venv`, así que `seed.py` funciona con ese intérprete.

### Comandos de Alembic

```bash
python -m alembic upgrade head
python -m alembic revision -m "mensaje"
python -m alembic downgrade -1
```

`python -m alembic revision -m "mensaje"` crea un nuevo archivo de migración en `alembic/versions/` con ese mensaje como nombre descriptivo. No aplica cambios en la base de datos; solo genera la plantilla para que escribas los cambios.

`python -m alembic downgrade -1` revierte la última migración aplicada. El `-1` significa "retrocede un paso".

Antes de levantar la API, ejecuta `python -m alembic upgrade head` para crear o actualizar las tablas.

## Estructura

- `app/auth/` autenticación y JWT
- `app/core/` configuración, base de datos y errores
- `app/models/` modelos ORM
- `app/routes/` endpoints
- `app/schemas/` modelos Pydantic
- `app/services/` lógica de negocio
- `app/utils/` utilidades
