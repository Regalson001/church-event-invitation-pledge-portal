from typing import Optional, Literal

from pydantic import BaseModel, EmailStr, Field, ConfigDict


class RSVPCreate(BaseModel):
    full_name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    phone: str = Field(default="", max_length=40)

    guests: int = Field(default=1, ge=1, le=20)

    attendance: Literal[
        "Attending",
        "Maybe",
        "Not attending"
    ] = "Attending"

    message: Optional[str] = Field(default="", max_length=1000)


class RSVPResponse(BaseModel):
    id: int
    full_name: str
    email: str
    guests: int
    attendance: str

    model_config = ConfigDict(from_attributes=True)


class PledgeCreate(BaseModel):
    full_name: str = Field(min_length=2, max_length=120)

    email: Optional[EmailStr] = None

    amount: float = Field(gt=0, le=100_000_000)

    currency: Literal["KES", "USD", "EUR"] = "KES"

    purpose: str = Field(
        default="General contribution",
        max_length=120
    )


class PledgeStatusUpdate(BaseModel):
    status: Literal[
        "Pledged",
        "Received",
        "Cancelled"
    ]
