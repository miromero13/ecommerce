# Women Style

Proyecto ecommerce (web) con backend en FastAPI y frontend en Angular.

## Estructura

- `backend/` - API construida con FastAPI, SQLAlchemy y PostgreSQL.
- `frontend/` - Aplicación web construida con Angular 21 y componentes Spartan/Helm.

---

## Backend

### Requisitos

- Python 3.10+
- PostgreSQL

### Instalación

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Variables de entorno

Crear un archivo `.env` en la raíz de `backend/`:

```env
DATABASE_URL=postgresql+psycopg2://usuario:clave@localhost:5432/tu_db
SECRET_KEY=tu_clave_secreta
ACCESS_TOKEN_EXPIRE_MINUTES=60
ALGORITHM=HS256
```

### Base de datos (migraciones)

```powershell
python -m alembic upgrade head
python -m alembic revision -m "mensaje"
python -m alembic downgrade -1
```

### Ejecutar

```powershell
uvicorn main:app --reload
```

Para exponer el servidor en todas las interfaces (emulador Android):

```powershell
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### Docs

- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`

---

## Frontend

### Requisitos

- Node.js 20 o superior
- npm 10 o superior

### Instalación

```powershell
cd frontend
npm install
```

### Ejecutar en desarrollo

```powershell
npm run start
```

Luego abre `http://localhost:4200/`.

Alternativa con Angular CLI:

```powershell
ng serve
```

### Comandos útiles

```powershell
npm run build
npm run watch
npm run test
```

- `npm run build`: genera la versión de producción.
- `npm run watch`: recompila en modo desarrollo al cambiar archivos.
- `npm run test`: ejecuta las pruebas del proyecto.