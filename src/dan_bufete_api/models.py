# src/dan_bufete_api/models.py

import enum
from datetime import datetime

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from dan_bufete_api.database import Base


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


class Case(Base):
    __tablename__ = "cases"

    id: Mapped[int] = mapped_column(primary_key=True)
    case_number: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text)
    client_name: Mapped[str] = mapped_column(String(255))
    lawyer_name: Mapped[str] = mapped_column(String(255))
    case_type: Mapped[str] = mapped_column(String(100))
    priority: Mapped[CasePriority] = mapped_column(default=CasePriority.MEDIUM)
    status: Mapped[CaseStatus] = mapped_column(default=CaseStatus.OPEN)

    opened_at: Mapped[datetime] = mapped_column(server_default=func.now())
    closed_at: Mapped[datetime | None] = mapped_column(default=None)

    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now()
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
    file_url: Mapped[str] = mapped_column(String(500))
    uploaded_by: Mapped[str] = mapped_column(String(255))
    uploaded_at: Mapped[datetime] = mapped_column(server_default=func.now())

    case: Mapped["Case"] = relationship(back_populates="documents")