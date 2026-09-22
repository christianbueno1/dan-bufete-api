# scripts/seed_db.py
"""
Seed de datos de prueba (10 Case) con personajes de la serie Suits.

Idempotente: cada caso se identifica por su `title`, que siempre termina en
el sufijo " [SEED]". Si un caso con ese título exacto ya existe, se omite —
se puede correr el script las veces que quieras sin duplicar datos.

Uso:
    uv run python scripts/seed_db.py
"""

from datetime import UTC, date, datetime, timedelta

from dan_bufete_api.database import Base, SessionLocal, engine
from dan_bufete_api.models import Case, CasePriority, CaseStatus, PracticeArea
from dan_bufete_api.routes import next_case_number

SEED_SUFFIX = " [SEED]"

today = date.today()
now = datetime.now(UTC)

SEED_CASES = [
    dict(
        practice_area=PracticeArea.COMMERCIAL,
        title="Fraud Allegations Defense",
        description="Defensa de Mike Ross frente a alegaciones de ejercicio ilegal de la abogacía.",
        client_name="Mike Ross",
        lawyer_name="Harvey Specter",
        priority=CasePriority.HIGH,
        status=CaseStatus.IN_PROGRESS,
        filing_date=today - timedelta(days=120),
        opened_at=now - timedelta(days=130),
    ),
    dict(
        practice_area=PracticeArea.LABOR,
        title="Partnership Dispute Mediation",
        description="Mediación de disputa societaria entre socios de la firma por Louis Litt.",
        client_name="Louis Litt",
        lawyer_name="Donna Paulsen",
        priority=CasePriority.MEDIUM,
        status=CaseStatus.OPEN,
        filing_date=None,
        opened_at=now - timedelta(days=10),
    ),
    dict(
        practice_area=PracticeArea.CIVIL,
        title="Firm Merger Litigation",
        description="Litigio derivado de la fusión de Pearson Hardman con Darby International.",
        client_name="Jessica Pearson",
        lawyer_name="Robert Zane",
        priority=CasePriority.HIGH,
        status=CaseStatus.CLOSED,
        filing_date=today - timedelta(days=400),
        opened_at=now - timedelta(days=410),
        closed_at=now - timedelta(days=30),
    ),
    dict(
        practice_area=PracticeArea.FAMILY,
        title="Estate Planning Consultation",
        description="Consultoría de planificación patrimonial para Rachel Zane.",
        client_name="Rachel Zane",
        lawyer_name="Katrina Bennett",
        priority=CasePriority.LOW,
        status=CaseStatus.OPEN,
        filing_date=None,
        opened_at=now - timedelta(days=5),
    ),
    dict(
        practice_area=PracticeArea.CRIMINAL,
        title="Embezzlement Investigation",
        description="Investigación por malversación de fondos contra Daniel Hardman.",
        client_name="Daniel Hardman",
        lawyer_name="Jessica Pearson",
        priority=CasePriority.HIGH,
        status=CaseStatus.ON_HOLD,
        filing_date=today - timedelta(days=200),
        opened_at=now - timedelta(days=210),
    ),
    dict(
        practice_area=PracticeArea.TAX,
        title="SEC Tax Fraud Inquiry",
        description="Investigación de la SEC por presunto fraude fiscal, liderada por Sean Cahill.",
        client_name="Sean Cahill",
        lawyer_name="Harvey Specter",
        priority=CasePriority.HIGH,
        status=CaseStatus.IN_PROGRESS,
        filing_date=today - timedelta(days=60),
        opened_at=now - timedelta(days=65),
    ),
    dict(
        practice_area=PracticeArea.COMMERCIAL,
        title="Hostile Takeover Defense",
        description="Defensa contra intento de adquisición hostil por Charles Forstman.",
        client_name="Charles Forstman",
        lawyer_name="Louis Litt",
        priority=CasePriority.MEDIUM,
        status=CaseStatus.CLOSED,
        filing_date=today - timedelta(days=500),
        opened_at=now - timedelta(days=510),
        closed_at=now - timedelta(days=100),
    ),
    dict(
        practice_area=PracticeArea.CIVIL,
        title="Breach of Contract Claim",
        description="Reclamo por incumplimiento de contrato presentado por Tara Messer.",
        client_name="Tara Messer",
        lawyer_name="Rachel Zane",
        priority=CasePriority.MEDIUM,
        status=CaseStatus.OPEN,
        filing_date=today - timedelta(days=15),
        opened_at=now - timedelta(days=20),
    ),
    dict(
        practice_area=PracticeArea.ADMINISTRATIVE,
        title="Regulatory Compliance Review",
        description="Revisión de cumplimiento regulatorio solicitada por Cameron Dennis.",
        client_name="Cameron Dennis",
        lawyer_name="Robert Zane",
        priority=CasePriority.LOW,
        status=CaseStatus.IN_PROGRESS,
        filing_date=None,
        opened_at=now - timedelta(days=25),
    ),
    dict(
        practice_area=PracticeArea.CONSTITUTIONAL,
        title="Firm Name Dispute Arbitration",
        description="Arbitraje por disputa sobre el uso del nombre de la firma, con Edward Darby.",
        client_name="Edward Darby",
        lawyer_name="Jessica Pearson",
        priority=CasePriority.MEDIUM,
        status=CaseStatus.CLOSED,
        filing_date=today - timedelta(days=600),
        opened_at=now - timedelta(days=610),
        closed_at=now - timedelta(days=200),
    ),
]


def seed() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    created = 0
    skipped = 0

    try:
        for data in SEED_CASES:
            title = data["title"] + SEED_SUFFIX

            exists = db.query(Case).filter(Case.title == title).first()
            if exists:
                skipped += 1
                continue

            case_number = next_case_number(db, data["practice_area"])

            case = Case(
                case_number=case_number,
                practice_area=data["practice_area"],
                title=title,
                description=data["description"],
                client_name=data["client_name"],
                lawyer_name=data["lawyer_name"],
                priority=data["priority"],
                status=data["status"],
                filing_date=data.get("filing_date"),
                opened_at=data["opened_at"],
                closed_at=data.get("closed_at"),
            )
            db.add(case)
            db.commit()
            created += 1
            print(f"  + {case_number}  {title}")

        print(f"\nListo. {created} casos creados, {skipped} ya existían.")
    finally:
        db.close()


if __name__ == "__main__":
    seed()