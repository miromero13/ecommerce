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

Para consumirla desde un Android Emulator, expón el servidor en todas las interfaces:

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

En Flutter usa `http://10.0.2.2:8000` como `BACKEND_URL`; `10.0.2.2` apunta al host desde el emulador Android.

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

- `alembic/versions/` contiene el historial canónico de migraciones.
- `seed.py` carga datos de demostración; no ejecutarlo sobre datos reales.
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

Para instalaciones gestionadas por Alembic, ejecuta `python -m alembic upgrade head` antes de levantar la API.

### Snapshot SQL: solamente para una base VACÍA

`database_schema.sql` permite crear las 37 tablas en PostgreSQL sin datos iniciales.
Incluye los tipos enum e índices del ORM y la pertenencia obligatoria de sucursales
con nombre único por empresa (migración 0038). Los clientes conservan identidad
global: `users.tenant_id` puede ser NULL y el email sigue siendo único globalmente.

Este snapshot **no equivale a haber aplicado Alembic**: no ejecuta los backfills,
seeders, ni registra `alembic_version`. Mantiene los defaults del snapshot ORM;
no reproduce todos los defaults de servidor de las migraciones. Alembic es la vía
canónica para instalaciones y actualizaciones de bases existentes. No combinar
ambas vías ciegamente: no ejecutar el SQL sobre una base con tablas ni hacer
`upgrade head` o `stamp head` sobre el snapshot sin reconciliar y verificar primero
su esquema y sus datos. No usar este archivo como migración de datos existentes.

### Pruebas del snapshot (PostgreSQL desechable)

Desde `backend/`, con PostgreSQL 16 local de prueba y `psycopg2` instalado:

```bash
CU1_TEST_DATABASE_URL=postgresql://postgres:cu1-disposable-only@127.0.0.1:53419/cu1_test PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -B -m pytest -p no:cacheprovider tests/test_database_schema.py
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -B -m pytest -p no:cacheprovider tests/test_natural_report_contract.py
```

La primera URL es exclusivamente para el contenedor desechable CU1; nunca usar
credenciales ni bases de trabajo. Las pruebas requieren explícitamente
`CU1_TEST_DATABASE_URL` (sin ella se omiten), rechazan destinos distintos de
`127.0.0.1/cu1_test` y no recurren a `DATABASE_URL` ni a `.env`. Cada prueba ejecuta
el SQL o el DDL de Branch en un schema temporal dentro de una transacción y hace
rollback al terminar; cada inserción rechazada usa savepoint y comprueba filas
sin cambios. No eliminan bases ni truncan tablas.

Estas pruebas no verifican todas las migraciones ni la API completa. La suite
completa y las pruebas SaaS que modifican datos necesitan un entorno y seed
independientes; su verificación queda pendiente para T4 de CU1.

## Estructura

- `app/auth/` autenticación y JWT
- `app/core/` configuración, base de datos y errores
- `app/models/` modelos ORM
- `app/routes/` endpoints
- `app/schemas/` modelos Pydantic
- `app/services/` lógica de negocio
- `app/utils/` utilidades
