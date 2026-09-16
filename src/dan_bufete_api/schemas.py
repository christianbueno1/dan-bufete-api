# src/dan_bufete_api/schemas.py

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict

from dan_bufete_api.models import CasePriority, CaseStatus, DocumentType, PracticeArea

# ---------- Case ----------


class CaseBase(BaseModel):
    practice_area: PracticeArea
    title: str
    description: str
    client_name: str
    lawyer_name: str
    priority: CasePriority = CasePriority.MEDIUM
    status: CaseStatus = CaseStatus.OPEN


class CaseCreate(CaseBase):
    filing_date: date | None = None
    opened_at: datetime | None = None


class CaseUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    client_name: str | None = None
    lawyer_name: str | None = None
    priority: CasePriority | None = None
    status: CaseStatus | None = None
    filing_date: date | None = None
    closed_at: datetime | None = None


class CaseRead(CaseBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    case_number: str
    filing_date: date | None
    opened_at: datetime
    closed_at: datetime | None
    created_at: datetime
    updated_at: datetime


class CaseReadWithDocuments(CaseRead):
    documents: list["CaseDocumentRead"] = []


# ---------- CaseDocument ----------


class CaseDocumentBase(BaseModel):
    name: str
    document_type: DocumentType
    file_url: str
    uploaded_by: str


class CaseDocumentCreate(CaseDocumentBase):
    pass


class CaseDocumentRead(CaseDocumentBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    case_id: int
    uploaded_at: datetime


CaseReadWithDocuments.model_rebuild()