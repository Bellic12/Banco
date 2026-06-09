from uuid import UUID
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from banco.users.models import Account, AccountStatus


class AccountRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, account_id: UUID) -> Account | None:
        result = await self.db.execute(select(Account).where(Account.id == account_id))
        return result.scalar_one_or_none()

    async def debit(self, account: Account, amount: Decimal) -> None:
        account.balance -= amount

    async def credit(self, account: Account, amount: Decimal) -> None:
        account.balance += amount
