# src/dan_bufete_api/models.py
import enum
from datetime import date, datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from dan_bufete_api.database import Base


class PracticeArea(str, enum.Enum):
    COMMERCIAL = "COMMERCIAL"
    CIVIL = "CIVIL"
    CRIMINAL = "CRIMINAL"
    LABOR = "LABOR"
    FAMILY = "FAMILY"
    ADMINISTRATIVE = "ADMINISTRATIVE"
    TAX = "TAX"
    CONSTITUTIONAL = "CONSTITUTIONAL"

    @property
    def code(self) -> str:
        return {
            PracticeArea.COMMERCIAL: "COM",
            PracticeArea.CIVIL: "CIV",
            PracticeArea.CRIMINAL: "CRI",
            PracticeArea.LABOR: "LAB",
            PracticeArea.FAMILY: "FAM",
            PracticeArea.ADMINISTRATIVE: "ADM",
            PracticeArea.TAX: "TAX",
            PracticeArea.CONSTITUTIONAL: "CON",
        }[self]


class CaseStatus(str, enum.Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    ON_HOLD = "on_hold"
    CLOSED = "closed"


class CasePriority(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class DocumentType(str, enum.Enum):
    CONTRACT = "contract"
    EVIDENCE = "evidence"
    COURT_FILING = "court_filing"
    CORRESPONDENCE = "correspondence"
    OTHER = "other"


class CaseNumberSequence(Base):
    """Contador atómico por (practice_area, year) para generar case_number."""

    __tablename__ = "case_number_sequences"

    practice_area: Mapped[PracticeArea] = mapped_column(primary_key=True)
    year: Mapped[int] = mapped_column(primary_key=True)
    last_value: Mapped[int] = mapped_column(default=0)


class Case(Base):
    __tablename__ = "cases"

    id: Mapped[int] = mapped_column(primary_key=True)
    case_number: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    practice_area: Mapped[PracticeArea]
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text)
    client_name: Mapped[str] = mapped_column(String(255))
    lawyer_name: Mapped[str] = mapped_column(String(255))
    priority: Mapped[CasePriority] = mapped_column(default=CasePriority.MEDIUM)
    status: Mapped[CaseStatus] = mapped_column(default=CaseStatus.OPEN)

    filing_date: Mapped[date | None] = mapped_column(default=None)
    opened_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    closed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), default=None
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    documents: Mapped[list["CaseDocument"]] = relationship(
        back_populates="case",
        cascade="all, delete-orphan",
    )


class CaseDocument(Base):
    __tablename__ = "case_documents"

    id: Mapped[int] = mapped_column(primary_key=True)
    case_id: Mapped[int] = mapped_column(ForeignKey("cases.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(255))
    document_type: Mapped[DocumentType]
    storage_key: Mapped[str] = mapped_column(String(500))   # antes: file_url
    uploaded_by: Mapped[str] = mapped_column(String(255))
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    case: Mapped["Case"] = relationship(back_populates="documents")
