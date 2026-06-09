from uuid import UUID
from decimal import Decimal
from pydantic import BaseModel
from banco.users.models import AccountStatus, AccountType


class AccountResponse(BaseModel):
    id: UUID
    owner_name: str
    balance: Decimal
    currency: str
    status: AccountStatus
    account_type: AccountType

    model_config = {"from_attributes": True}
