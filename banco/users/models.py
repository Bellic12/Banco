import uuid
from decimal import Decimal
from sqlalchemy import String, Numeric, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID
import enum
from banco.db.base import Base


class AccountStatus(str, enum.Enum):
    active = "active"
    inactive = "inactive"


class AccountType(str, enum.Enum):
    user = "user"
    airline = "airline"
    insurer = "insurer"


class Account(Base):
    __tablename__ = "accounts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    owner_name: Mapped[str] = mapped_column(String(255), nullable=False)
    balance: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False, default=Decimal("0.00"))
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")
    status: Mapped[AccountStatus] = mapped_column(SAEnum(AccountStatus), nullable=False, default=AccountStatus.active)
    account_type: Mapped[AccountType] = mapped_column(SAEnum(AccountType), nullable=False, default=AccountType.user)
