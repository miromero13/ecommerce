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

### Autorización con asignaciones actuales

El JWT mantiene su formato; en cada petición protegida se usan el rol, la empresa
y la sucursal actuales del usuario en la base, no sus asignaciones históricas del
token. Un cambio de asignación no invalida por sí solo el token. Se conservan los
roles permitidos por cada ruta; el superadministrador no recibe acceso implícito
a rutas reservadas a otros roles. Clientes y superadministradores siguen siendo
globales y pueden conservar `tenant_id=NULL`; las lecturas públicas no cambian.

Los empleados sin empresa reciben 403 `Usuario sin empresa asociada`. Encargado,
cajero y delivery requieren sucursal: 403 `Usuario operativo sin sucursal asignada`
si falta, o `La sucursal no existe o está inactiva en esta empresa` si no pertenece
a su empresa o está inactiva. Se mantienen 401 `Token inválido` / `Usuario no encontrado`,
403 `Usuario inactivo` y `No tienes permisos para acceder a este recurso`.
Los errores usan el contrato existente `{statusCode, message, error}`.

Prueba API aislada, desde `backend/`, **solo** con el contenedor desechable CU1:

```bash
CU1_TEST_DATABASE_URL=postgresql://postgres:cu1-disposable-only@127.0.0.1:53419/cu1_test PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -B -m pytest -p no:cacheprovider tests/test_employee_authorization.py
```

El fixture exige ese destino local explícito, no carga `.env` ni credenciales
opcionales, monta las rutas reales bajo `/api` con sus manejadores de errores y
reemplaza únicamente `get_db`. Usa schema temporal y transacción exterior con
savepoints (`join_transaction_mode=create_savepoint`): los commits/rollbacks de
la aplicación no persisten fuera de la prueba. No inicia lifespan ni servicios
externos. El schema vacío UUID se crea una vez por sesión de pytest y se elimina
solo ese schema al terminar. Cada prueba conserva rollback exterior; cada petición
abre y cierra su propia Session con savepoint, para detectar escrituras sin commit.
Estas pruebas no demuestran aislamiento completo de inventario, BI ni compras.

### Aislamiento de catálogo (CU1)

Los listados privados `/api/catalog/products/admin` y `/products/pending` usan la
empresa persistida del administrador; ni el JWT histórico ni `?tenant_id=` cambian
ese alcance. Los escritores administrativos validan producto, variante, categoría,
temporada, colección, proveedor y sucursal antes de modificar datos o imágenes.
Un destino ajeno responde 404 con el mismo estilo de un destino inexistente,
salvo la referencia de proveedor al crear/editar productos: conserva el contrato
400 `El proveedor no existe`, tanto si no existe como si pertenece a otra empresa.
Productos, variantes y taxonomías nuevas reciben empresa; las variantes nuevas
heredan la del producto. Las mutaciones de producto confirman su transacción.
El setter legado de inventario conserva reservas y mínimos; no sustituye las
operaciones del módulo de inventario.

`provider-submission` usa el perfil proveedor del usuario actual y exige que
pertenezca a su empresa; ignora `provider_id` enviado y fuerza variantes pendientes.
La calibración `PATCH /api/catalog/variants/{id}/garment-points` requiere
administrador y variante propia, como los demás escritores del catálogo.

Tallas y colores siguen siendo referencias globales: GET público, pero POST,
PUT y DELETE requieren `superadministrador` (403 para administradores de empresa).
Se conservan las restricciones de eliminación de referencias en uso. La página
administrativa muestra esas listas en solo lectura y conserva las selecciones en
productos; la plataforma puede mantenerlas con Swagger. El catálogo público y
las lecturas de clientes siguen incluyendo empresas distintas.

Prueba focalizada desde `backend/` (solo PostgreSQL desechable autorizado):

```bash
CU1_TEST_DATABASE_URL=postgresql://postgres:cu1-disposable-only@127.0.0.1:53419/cu1_test PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -B -m pytest -p no:cacheprovider tests/test_catalog_tenant_isolation.py --tb=short
```

La batería de catálogo y regresión aprobó 163 casos; después del ajuste de
compatibilidad aprobaron 8 casos dirigidos. Angular compiló correctamente.
Esto no equivale a validar CU1 completo.

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
