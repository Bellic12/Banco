"""Run once to create tables and seed system accounts."""
import asyncio
import uuid
from decimal import Decimal
from banco.db.base import engine, Base
from banco.config import settings
from banco.users.models import Account, AccountStatus, AccountType
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import async_sessionmaker

AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


async def seed():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as session:
        airline = Account(
            id=settings.airline_account_id,
            owner_name="Airline",
            balance=Decimal("0.00"),
            currency="USD",
            status=AccountStatus.active,
            account_type=AccountType.airline,
        )
        insurer = Account(
            id=settings.insurer_account_id,
            owner_name="Insurance Company",
            balance=Decimal("0.00"),
            currency="USD",
            status=AccountStatus.active,
            account_type=AccountType.insurer,
        )
        test_user = Account(
            id=uuid.uuid4(),
            owner_name="Test User",
            balance=Decimal("5000.00"),
            currency="USD",
            status=AccountStatus.active,
            account_type=AccountType.user,
        )
        session.add_all([airline, insurer, test_user])
        await session.commit()
        print(f"Seeded. Test user account ID: {test_user.id}")


if __name__ == "__main__":
    asyncio.run(seed())
