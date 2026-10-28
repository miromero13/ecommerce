from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_tenant_id, require_roles
from app.core.database import SessionLocal, get_db
from app.schemas.enums import RolEnum
from app.schemas.rpa_ingest_schema import ItemsCorrection, JobCommit
from app.services import rpa_ingest_service as service
from app.utils.response import response


router = APIRouter(prefix="/rpa/ingest", tags=["RPA Ingest"])
UPLOADERS = require_roles(RolEnum.proveedor, RolEnum.administrador, RolEnum.encargado)
COMMITTERS = require_roles(RolEnum.administrador, RolEnum.encargado)


def get_session_factory():
    """Session source for background processing (overridden in tests)."""
    return SessionLocal


def _job(db: Session, job_id: UUID, user: dict, tenant_id: UUID):
    try:
        return service.get_job(db, job_id, tenant_id=tenant_id, user_id=UUID(user["sub"]), rol=user["rol"])
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post("/upload-document", status_code=status.HTTP_202_ACCEPTED)
async def upload_document_route(
    background: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: dict = Depends(UPLOADERS),
    tenant_id: UUID = Depends(get_current_tenant_id),
    session_factory=Depends(get_session_factory),
):
    content = await file.read()
    try:
        service.validate_upload(content, file.content_type)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    job = service.create_job(db, tenant_id=tenant_id, user_id=UUID(user["sub"]),
                             filename=file.filename or "documento", content_type=file.content_type)
    background.add_task(service.process_job, session_factory, job.id, content)
    return response(status_code=status.HTTP_202_ACCEPTED, message="Documento recibido. Extracción RPA en proceso.",
                    data={"job_id": job.id, "filename": job.filename, "status": job.status})


@router.get("/jobs")
def list_jobs_route(db: Session = Depends(get_db), user: dict = Depends(UPLOADERS),
                    tenant_id: UUID = Depends(get_current_tenant_id)):
    jobs = service.list_jobs(db, tenant_id=tenant_id, user_id=UUID(user["sub"]), rol=user["rol"])
    return response(status_code=200, message="Documentos obtenidos", data=[service.serialize(job) for job in jobs])


@router.get("/jobs/{job_id}")
def get_job_route(job_id: UUID, db: Session = Depends(get_db), user: dict = Depends(UPLOADERS),
                  tenant_id: UUID = Depends(get_current_tenant_id)):
    job = _job(db, job_id, user, tenant_id)
    if job.status == "failed":
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=job.error_message)
    return response(status_code=200, message="Resultado de extracción obtenido", data=service.serialize(job))


@router.patch("/jobs/{job_id}/items")
def correct_items_route(job_id: UUID, payload: ItemsCorrection, db: Session = Depends(get_db),
                        user: dict = Depends(UPLOADERS), tenant_id: UUID = Depends(get_current_tenant_id)):
    job = _job(db, job_id, user, tenant_id)
    try:
        job = service.correct_items(db, job, payload.items)
    except service.JobConflict as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return response(status_code=200, message="Ítems del documento actualizados", data=service.serialize(job))


@router.post("/jobs/{job_id}/commit", status_code=status.HTTP_201_CREATED)
def commit_job_route(job_id: UUID, payload: JobCommit, db: Session = Depends(get_db),
                     user: dict = Depends(COMMITTERS), tenant_id: UUID = Depends(get_current_tenant_id)):
    job = _job(db, job_id, user, tenant_id)
    # A branch manager only receives goods into their own branch.
    if user["rol"] == RolEnum.encargado.value and str(payload.branch_id) != user.get("branch_id"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tienes permisos para esta sucursal")
    try:
        data = service.commit_job(db, job, branch_id=payload.branch_id, user_id=UUID(user["sub"]))
    except service.JobConflict as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return response(status_code=201, message="Mercadería ingresada al inventario y catálogo sincronizado exitosamente",
                    data=data)
