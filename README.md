# Women Style

Proyecto ecommerce (web) con backend en FastAPI y frontend en Angular.

## Estructura

- `backend/` - API construida con FastAPI, SQLAlchemy y PostgreSQL.
- `frontend/` - Aplicación web construida con Angular 21 y componentes Spartan/Helm.

---

## Requisitos

| Componente | Requisito |
|---|---|
| Backend | Python **3.12** (o 3.13). PostgreSQL (servicio corriendo). |
| Frontend | Node **20.19+** o **22.13+** (lo valida `frontend/scripts/check-node.mjs`). npm 10+. |

> **Importante:** usa Python 3.12, **no 3.14**. El `requirements.txt` contiene
> versiones fijadas improntas que no tienen binarios (wheels) para 3.14 y
> intentarían compilarse desde código fuente (error de MSVC / `cffi`).

---

## Backend

### 1. Primera vez

Abrir una terminal en `backend/`, crear el entorno virtual, instalar dependencias
y preparar la base de datos:

```powershell
cd backend
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

> En **cmd.exe** usa `.venv\Scripts\activate.bat` en vez de `Activate.ps1`.
> Si te sale un prompt con `(.venv)` al inicio, el entorno está activo.

Crear el archivo `.env` (copia de `backend\.env.example`):

```powershell
Copy-Item .env.example .env
```

Editar `.env` y poner al menos:

```env
DATABASE_URL=postgresql+psycopg2://postgres:TU_PASSWORD@localhost:5432/tu_db
SECRET_KEY=tu_clave_secreta
ACCESS_TOKEN_EXPIRE_MINUTES=60
ALGORITHM=HS256
```

Crea la base de datos indicada en `DATABASE_URL` si aún no existe
(por ejemplo `tu_db`), luego construye el esquema y puebla con datos demo:

```powershell
python -m alembic upgrade head
python seed.py
```

### 2. Siguientes veces

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
python -m alembic upgrade head   # si hubo migraciones nuevas
python -m uvicorn main:app --reload
```

La API queda en `http://127.0.0.1:8000`.

- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`

### Credenciales demo

`seed.py` crea cuentas demo; todas usan la contraseña **`Fashion123!`**:

- Admin global: `admin.global@fashionstore.bo`
- Admin sucursal: `admin.lp@fashionstore.bo`, `admin.sc@fashionstore.bo`, `admin.cbba@fashionstore.bo`
- Encargados: `encargada.lp@fashionstore.bo`, `encargado.sc@fashionstore.bo`, `encargado.cbba@fashionstore.bo`
- Cajeros: `cajera.lp@fashionstore.bo`, `cajero.sc@fashionstore.bo`, `cajera.cbba@fashionstore.bo`
- Delivery: `delivery1@fashionstore.bo`, `delivery2@fashionstore.bo`
- Cliente: `cliente01.demo@fashionstore.bo`

### Comandos útiles de migraciones

```powershell
python -m alembic upgrade head   # aplica migraciones
python -m alembic revision -m "mensaje"   # crea una migración nueva
python -m alembic downgrade -1   # revierte la última
```

---

## Frontend

### Versión de Node

La app exige Node **20.19+** o **22.13+** (lo valida `scripts/check-node.mjs`).
Si tienes otra versión (por ejemplo v26), `npm run start` fallará con:

```
[frontend] Version de Node no compatible con esta app.
[frontend] Detectada: v26.1.0
[frontend] Requerida: v20.19.x o v22.13.x+
```

Para cambiarla a Node 22 (PowerShell):

**Cambiar en la terminal actual:**

```powershell
$env:Path = "C:\Users\PERSONAL\AppData\Roaming\fnm\node-versions\v22.13.1\installation;" + $env:Path; node -v
```

Debe mostrar `v22.13.1`.

**Cambiarla de forma permanente** (así toda terminal nueva ya abre con Node 22):

```powershell
New-Item -ItemType File -Force $PROFILE | Out-Null
Add-Content $PROFILE '$env:Path = "C:\Users\PERSONAL\AppData\Roaming\fnm\node-versions\v22.13.1\installation;" + $env:Path'
```

### 1. Primera vez

```powershell
cd frontend
npm install --legacy-peer-deps
```

> Usa `--legacy-peer-deps` por el conflicto de peers de `angular-chrts`
> (librería de gráficas que pide Angular 19, mientras el proyecto es Angular 21).

> **Si una instalación se corta a mitad**, borra `node_modules` antes de
> reinstalar o quedarán archivos corruptos:
> `Remove-Item -Recurse -Force node_modules; npm install --legacy-peer-deps`

### 2. Siguientes veces

```powershell
cd frontend
npm run start
```

Luego abre `http://localhost:4200/`.

El frontend llama a la API en `http://localhost:8000/api`
(definido en `frontend/src/environments/environment.ts`). Asegúrate de que el
backend esté corriendo.

### Emulador Android

Para consumir desde un emulador Android, expón el backend en todas las interfaces
y usa `10.0.2.2` como host desde el emulador:

```powershell
cd backend
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Y en el frontend, reemplaza el `apiBaseUrl` (en `environment.ts` o el
`runtimeConfig` de `public/runtime-config.js`) por
`http://10.0.2.2:8000/api`.

---

## Resumen rápido

| Acción | Comandos |
|---|---|
| Backend (primera vez) | `py -3.12 -m venv .venv` → `.\.venv\Scripts\Activate.ps1` → `pip install -r requirements.txt` → crear `.env` → `python -m alembic upgrade head` → `python seed.py` |
| Backend (siguiente) | `.\.venv\Scripts\Activate.ps1` → `python -m uvicorn main:app --reload` |
| Frontend (primera vez) | `npm install --legacy-peer-deps` |
| Frontend (siguiente) | `npm run start` |
| Poblar base de datos | `python seed.py` |

---

## Notas

- Las tablas **no** se crean automáticamente al arrancar la API; ejecuta antes
  `python -m alembic upgrade head`.
- Si `alembic` no es el binario del venv, usa `python -m alembic`.
- Backend: `app/auth/`, `app/core/`, `app/models/`, `app/routes/`,
  `app/schemas/`, `app/services/`, `app/utils/`.
- Frontend: `src/app/shared/` (auth, perfil, guards), `src/app/features/`
  (admin, cliente, cajero, proveedor, encargado, delivery).