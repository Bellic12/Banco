from uuid import UUID
from decimal import Decimal
from datetime import datetime
from pydantic import BaseModel, field_validator
from banco.transactions.models import TransactionType, TransactionStatus


class PaymentRequest(BaseModel):
    user_account_id: UUID
    amount: Decimal
    currency: str = "USD"
    reference: str

    @field_validator("amount")
    @classmethod
    def amount_must_be_positive(cls, v: Decimal) -> Decimal:
        if v <= 0:
            raise ValueError("amount must be positive")
        return v


class TransactionResponse(BaseModel):
    id: UUID
    type: TransactionType
    status: TransactionStatus
    amount: Decimal
    currency: str
    from_account_id: UUID
    to_account_id: UUID
    reference: str
    failure_reason: str | None
    timestamp: datetime

    model_config = {"from_attributes": True}


class TransactionListResponse(BaseModel):
    reference: str
    transactions: list[TransactionResponse]
