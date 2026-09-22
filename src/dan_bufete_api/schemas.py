# src/dan_bufete_api/schemas.py

from datetime import UTC, date, datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from dan_bufete_api.models import CasePriority, CaseStatus, DocumentType, PracticeArea

# ---------- Case ----------


class CaseBase(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    practice_area: PracticeArea
    title: str = Field(min_length=3, max_length=255)
    description: str = Field(min_length=10)
    client_name: str = Field(min_length=2, max_length=255)
    lawyer_name: str = Field(min_length=2, max_length=255)
    priority: CasePriority = CasePriority.MEDIUM
    status: CaseStatus = CaseStatus.OPEN


class CaseCreate(CaseBase):
    filing_date: date | None = None
    opened_at: datetime | None = None

    @field_validator("filing_date")
    @classmethod
    def filing_date_not_future(cls, value: date | None) -> date | None:
        if value is not None and value > date.today():
            raise ValueError("filing_date cannot be in the future")
        return value

    @field_validator("opened_at")
    @classmethod
    def opened_at_not_future(cls, value: datetime | None) -> datetime | None:
        if value is not None and value > datetime.now(UTC):
            raise ValueError("opened_at cannot be in the future")
        return value


class CaseUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    title: str | None = Field(default=None, min_length=3, max_length=255)
    description: str | None = Field(default=None, min_length=10)
    client_name: str | None = Field(default=None, min_length=2, max_length=255)
    lawyer_name: str | None = Field(default=None, min_length=2, max_length=255)
    priority: CasePriority | None = None
    status: CaseStatus | None = None
    filing_date: date | None = None
    closed_at: datetime | None = None

    @field_validator("filing_date")
    @classmethod
    def filing_date_not_future(cls, value: date | None) -> date | None:
        if value is not None and value > date.today():
            raise ValueError("filing_date cannot be in the future")
        return value


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
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(min_length=1, max_length=255)
    document_type: DocumentType
    uploaded_by: str = Field(min_length=2, max_length=255)


class CaseDocumentRead(CaseDocumentBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    case_id: int
    file_url: str
    uploaded_at: datetime


CaseReadWithDocuments.model_rebuild()