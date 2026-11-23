from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Float,
    Text,
    CheckConstraint
)
from sqlalchemy.sql import func

from .database import Base


class RSVP(Base):
    __tablename__ = "rsvps"

    id = Column(Integer, primary_key=True, index=True)

    full_name = Column(String(120), nullable=False)
    email = Column(String(180), nullable=False, index=True)
    phone = Column(String(40), default="")

    guests = Column(Integer, nullable=False, default=1)
    attendance = Column(String(20), nullable=False, default="Attending")

    message = Column(Text, default="")

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    __table_args__ = (
        CheckConstraint("guests >= 1 AND guests <= 20"),
    )


class Pledge(Base):
    __tablename__ = "pledges"

    id = Column(Integer, primary_key=True, index=True)

    full_name = Column(String(120), nullable=False)
    email = Column(String(180), default="")

    amount = Column(Float, nullable=False)
    currency = Column(String(8), nullable=False, default="KES")

    purpose = Column(
        String(120),
        nullable=False,
        default="General contribution"
    )

    status = Column(
        String(20),
        nullable=False,
        default="Pledged"
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    __table_args__ = (
        CheckConstraint("amount > 0"),
    )
