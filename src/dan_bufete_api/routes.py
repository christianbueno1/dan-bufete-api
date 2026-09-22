# src/dan_bufete_api/routes.py

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Form, File, HTTPException, UploadFile, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from dan_bufete_api import models, schemas
from dan_bufete_api.database import get_db
from dan_bufete_api.storage import get_storage_backend, StorageBackend

router = APIRouter()


# ---------- case_number generation ----------


def next_case_number(
    db: Session, practice_area: models.PracticeArea, year: int | None = None
) -> str:
    year = year or datetime.now().year

    result = db.execute(
        text("""
            INSERT INTO case_number_sequences (practice_area, year, last_value)
            VALUES (:area, :year, 1)
            ON CONFLICT (practice_area, year)
            DO UPDATE SET last_value = case_number_sequences.last_value + 1
            RETURNING last_value
        """),
        {"area": practice_area.value, "year": year},
    )
    seq = result.scalar_one()
    return f"{practice_area.code}-{year}-{seq:04d}"


# ---------- helpers ----------


def get_case_or_404(db: Session, case_id: int) -> models.Case:
    case = db.get(models.Case, case_id)
    if case is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Case not found")
    return case


# ---------- Case ----------


@router.post(
    "/cases", response_model=schemas.CaseRead, status_code=status.HTTP_201_CREATED
)
def create_case(payload: schemas.CaseCreate, db: Session = Depends(get_db)):
    case_number = next_case_number(db, payload.practice_area)

    case = models.Case(
        case_number=case_number,
        opened_at=payload.opened_at or datetime.now(UTC),
        **payload.model_dump(exclude={"opened_at"}),
    )
    db.add(case)
    db.commit()
    db.refresh(case)
    return case


@router.get("/cases", response_model=list[schemas.CaseRead])
def list_cases(
    db: Session = Depends(get_db),
    practice_area: models.PracticeArea | None = None,
    status_: models.CaseStatus | None = None,
    skip: int = 0,
    limit: int = 100,
):
    query = db.query(models.Case)
    if practice_area is not None:
        query = query.filter(models.Case.practice_area == practice_area)
    if status_ is not None:
        query = query.filter(models.Case.status == status_)
    return query.offset(skip).limit(limit).all()


@router.get("/cases/{case_id}", response_model=schemas.CaseReadWithDocuments)
def get_case(
    case_id: int,
    db: Session = Depends(get_db),
    storage: StorageBackend = Depends(get_storage_backend),
):
    case = get_case_or_404(db, case_id)
    return schemas.CaseReadWithDocuments(
        **schemas.CaseRead.model_validate(case).model_dump(),
        documents=[to_document_read(d, storage) for d in case.documents],
    )


@router.patch("/cases/{case_id}", response_model=schemas.CaseRead)
def update_case(
    case_id: int, payload: schemas.CaseUpdate, db: Session = Depends(get_db)
):
    case = get_case_or_404(db, case_id)
    updates = payload.model_dump(exclude_unset=True)

    if "closed_at" in updates and updates["closed_at"] is not None:
        if updates["closed_at"] < case.opened_at:
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                "closed_at cannot be earlier than opened_at",
            )

    if updates.get("status") == models.CaseStatus.CLOSED and case.closed_at is None:
        updates["closed_at"] = datetime.now(UTC)

    for field, value in updates.items():
        setattr(case, field, value)

    db.commit()
    db.refresh(case)
    return case


@router.delete("/cases/{case_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_case(case_id: int, db: Session = Depends(get_db)):
    case = get_case_or_404(db, case_id)
    db.delete(case)
    db.commit()

# ---- Document -----

def to_document_read(
    document: models.CaseDocument, storage: StorageBackend
) -> schemas.CaseDocumentRead:
    return schemas.CaseDocumentRead(
        id=document.id,
        case_id=document.case_id,
        name=document.name,
        document_type=document.document_type,
        uploaded_by=document.uploaded_by,
        uploaded_at=document.uploaded_at,
        file_url=storage.get_url(document.storage_key),
    )


@router.get("/cases/{case_id}/documents", response_model=list[schemas.CaseDocumentRead])
def list_case_documents(
    case_id: int,
    db: Session = Depends(get_db),
    storage: StorageBackend = Depends(get_storage_backend),
):
    get_case_or_404(db, case_id)
    documents = (
        db.query(models.CaseDocument)
        .filter(models.CaseDocument.case_id == case_id)
        .all()
    )
    return [to_document_read(d, storage) for d in documents]


@router.delete(
    "/cases/{case_id}/documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT
)
def delete_case_document(
    case_id: int,
    document_id: int,
    db: Session = Depends(get_db),
    storage: StorageBackend = Depends(get_storage_backend),
):
    document = (
        db.query(models.CaseDocument)
        .filter(
            models.CaseDocument.id == document_id,
            models.CaseDocument.case_id == case_id,
        )
        .first()
    )
    if document is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Document not found")

    storage.delete(document.storage_key)
    db.delete(document)
    db.commit()


@router.post(
    "/cases/{case_id}/documents/upload",
    response_model=schemas.CaseDocumentRead,
    status_code=status.HTTP_201_CREATED,
)
def upload_case_document(
    case_id: int,
    file: UploadFile,
    document_type: models.DocumentType = Form(...),
    uploaded_by: str = Form(...),
    name: str | None = Form(None),
    db: Session = Depends(get_db),
    storage: StorageBackend = Depends(get_storage_backend),
):
    get_case_or_404(db, case_id)

    storage_key = storage.save(file)

    document = models.CaseDocument(
        case_id=case_id,
        name=name or file.filename or "untitled",
        document_type=document_type,
        storage_key=storage_key,
        uploaded_by=uploaded_by,
    )
    db.add(document)
    db.commit()
    db.refresh(document)
    return to_document_read(document, storage)
