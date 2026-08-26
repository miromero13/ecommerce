from fastapi import Request, FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi import HTTPException  #  Úsala para lanzar errores de negocio
from starlette.exceptions import HTTPException as StarletteHTTPException
from app.utils.response import response
import traceback

def register_error_handlers(app: FastAPI):
    # Maneja todas las HTTPException (incluye las que tú lances)
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        return response(
            status_code=exc.status_code,
            message=exc.detail if hasattr(exc, "detail") else str(exc),
            error=exc.__class__.__name__,
        )

    # Maneja errores de validación en query/body/path
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        return response(
            status_code=422,
            message="Error de validación en los datos enviados",
            error=exc.errors(),
        )

    # Maneja errores inesperados del servidor
    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception):
        traceback.print_exc()  # 👈 Útil para debug en consola
        return response(
            status_code=500,
            message="Error interno del servidor",
            error=str(exc),
        )
