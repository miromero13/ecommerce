from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware

from app.routes import user_routes, auth, branch_routes, provider_routes
from app.core.error_handlers import register_error_handlers

app = FastAPI(title="ACI")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
api_router = APIRouter(prefix="/api")
api_router.include_router(user_routes.router)
api_router.include_router(auth.router)  
api_router.include_router(branch_routes.router)
api_router.include_router(provider_routes.router)

app.include_router(api_router)

register_error_handlers(app)
