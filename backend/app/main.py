from contextlib import asynccontextmanager
from datetime import datetime, timezone
import io

from fastapi import (
    FastAPI,
    Depends,
    HTTPException,
    status
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from .database import Base, engine, get_db
from . import models, schemas
from .security import require_admin
from .services import get_event_summary, create_csv_report


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="Gather & Give API",
    description="Event invitations, RSVPs and pledge management.",
    version="1.0.0",
    lifespan=lifespan
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5500",
        "http://localhost:5500"
    ],
    allow_credentials=False,
    allow_methods=["GET", "POST", "PATCH"],
    allow_headers=["Content-Type", "X-Admin-Key"]
)


@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "application": "Gather & Give"
    }


@app.post(
    "/api/rsvps",
    status_code=status.HTTP_201_CREATED
)
def create_rsvp(
    payload: schemas.RSVPCreate,
    db: Session = Depends(get_db)
):
    existing = (
        db.query(models.RSVP)
        .filter(models.RSVP.email == payload.email)
        .first()
    )

    if existing:
        raise HTTPException(
            status_code=409,
            detail="An RSVP already exists for this email address."
        )

    record = models.RSVP(**payload.model_dump())

    db.add(record)
    db.commit()
    db.refresh(record)

    return {
        "message": "Your RSVP has been received.",
        "id": record.id
    }


@app.post(
    "/api/pledges",
    status_code=status.HTTP_201_CREATED
)
def create_pledge(
    payload: schemas.PledgeCreate,
    db: Session = Depends(get_db)
):
    record = models.Pledge(
        **payload.model_dump(exclude_none=True)
    )

    db.add(record)
    db.commit()
    db.refresh(record)

    return {
        "message": "Your pledge has been recorded.",
        "id": record.id
    }


@app.get("/api/public/summary")
def public_summary(
    db: Session = Depends(get_db)
):
    return get_event_summary(db)


@app.get(
    "/api/admin/rsvps",
    dependencies=[Depends(require_admin)]
)
def get_rsvps(
    db: Session = Depends(get_db)
):
    records = (
        db.query(models.RSVP)
        .order_by(models.RSVP.created_at.desc())
        .all()
    )

    return [
        {
            "id": record.id,
            "full_name": record.full_name,
            "email": record.email,
            "phone": record.phone,
            "guests": record.guests,
            "attendance": record.attendance,
            "message": record.message,
            "created_at": str(record.created_at)
        }
        for record in records
    ]


@app.get(
    "/api/admin/pledges",
    dependencies=[Depends(require_admin)]
)
def get_pledges(
    db: Session = Depends(get_db)
):
    records = (
        db.query(models.Pledge)
        .order_by(models.Pledge.created_at.desc())
        .all()
    )

    return [
        {
            "id": record.id,
            "full_name": record.full_name,
            "email": record.email,
            "amount": record.amount,
            "currency": record.currency,
            "purpose": record.purpose,
            "status": record.status,
            "created_at": str(record.created_at)
        }
        for record in records
    ]


@app.patch(
    "/api/admin/pledges/{pledge_id}",
    dependencies=[Depends(require_admin)]
)
def update_pledge_status(
    pledge_id: int,
    payload: schemas.PledgeStatusUpdate,
    db: Session = Depends(get_db)
):
    record = (
        db.query(models.Pledge)
        .filter(models.Pledge.id == pledge_id)
        .first()
    )

    if not record:
        raise HTTPException(
            status_code=404,
            detail="Pledge not found."
        )

    record.status = payload.status

    db.commit()

    return {
        "message": "Pledge status updated."
    }


@app.get(
    "/api/admin/export/{report_type}",
    dependencies=[Depends(require_admin)]
)
def export_report(
    report_type: str,
    db: Session = Depends(get_db)
):
    if report_type == "rsvps":
        records = db.query(models.RSVP).all()

        fields = [
            "id",
            "full_name",
            "email",
            "phone",
            "guests",
            "attendance",
            "message",
            "created_at"
        ]

    elif report_type == "pledges":
        records = db.query(models.Pledge).all()

        fields = [
            "id",
            "full_name",
            "email",
            "amount",
            "currency",
            "purpose",
            "status",
            "created_at"
        ]

    else:
        raise HTTPException(
            status_code=404,
            detail="Unknown report type."
        )

    output = create_csv_report(records, fields)

    filename = f"{report_type}-report.csv"

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition": (
                f'attachment; filename="{filename}"'
            )
        }
    )
