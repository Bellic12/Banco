import uuid
from decimal import Decimal
from datetime import datetime, timezone
from sqlalchemy import String, Numeric, Enum as SAEnum, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID
import enum
from banco.db.base import Base


class TransactionType(str, enum.Enum):
    flight = "flight"
    insurance = "insurance"


class TransactionStatus(str, enum.Enum):
    pending = "PENDING"
    success = "SUCCESS"
    failed = "FAILED"


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    type: Mapped[TransactionType] = mapped_column(SAEnum(TransactionType), nullable=False)
    status: Mapped[TransactionStatus] = mapped_column(SAEnum(TransactionStatus), nullable=False, default=TransactionStatus.pending)
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    from_account_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("accounts.id"), nullable=False)
    to_account_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("accounts.id"), nullable=False)
    reference: Mapped[str] = mapped_column(String(255), nullable=False)
    failure_reason: Mapped[str | None] = mapped_column(String(500), nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
