from uuid import UUID
from decimal import Decimal
from datetime import datetime
from pydantic import BaseModel, field_validator
from banco.transactions.models import TransactionType, TransactionStatus


class PaymentRequest(BaseModel):
    user_account_id: UUID
    flight_amount: Decimal
    insurance_amount: Decimal = Decimal("0.00")

    @field_validator("flight_amount")
    @classmethod
    def flight_must_be_positive(cls, v: Decimal) -> Decimal:
        if v <= 0:
            raise ValueError("flight_amount must be positive")
        return v

    @field_validator("insurance_amount")
    @classmethod
    def insurance_must_be_non_negative(cls, v: Decimal) -> Decimal:
        if v < 0:
            raise ValueError("insurance_amount must be non-negative")
        return v


class PaymentResponse(BaseModel):
    success: bool


class TransactionResponse(BaseModel):
    id: UUID
    type: TransactionType
    status: TransactionStatus
    amount: Decimal
    from_account_id: UUID
    to_account_id: UUID
    failure_reason: str | None
    timestamp: datetime

    model_config = {"from_attributes": True}


class TransactionListResponse(BaseModel):
    transactions: list[TransactionResponse]
