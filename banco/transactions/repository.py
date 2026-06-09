from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from banco.transactions.models import Transaction


class TransactionRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, transaction: Transaction) -> Transaction:
        self.db.add(transaction)
        return transaction

    async def get_by_id(self, transaction_id: UUID) -> Transaction | None:
        result = await self.db.execute(select(Transaction).where(Transaction.id == transaction_id))
        return result.scalar_one_or_none()

    async def get_by_reference(self, reference: str) -> list[Transaction]:
        result = await self.db.execute(select(Transaction).where(Transaction.reference == reference))
        return list(result.scalars().all())
