"""Run once to create tables and seed system accounts."""
import asyncio
import uuid
from decimal import Decimal
from banco.db.base import engine, Base
from banco.config import settings
from banco.users.models import Account, AccountStatus, AccountType
from sqlalchemy.ext.asyncio import async_sessionmaker

AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)

USER_1_ID = uuid.UUID("00000000-0000-0000-0000-000000000003")
BROKE_USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000004")

DUMMY_USERS = [
    ("Alice Johnson",  Decimal("8500.00")),
    ("Bob Martinez",   Decimal("3200.00")),
    ("Carol Smith",    Decimal("12000.00")),
    ("David Lee",      Decimal("450.00")),
    ("Eva Torres",     Decimal("6750.00")),
]


async def seed():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as session:
        user_1 = Account(
            id=USER_1_ID,
            owner_name="User 1",
            balance=Decimal("10000.00"),
            currency="USD",
            status=AccountStatus.active,
            account_type=AccountType.user,
        )

        system_accounts = [
            Account(
                id=settings.airline_account_id,
                owner_name="SkyWings Airlines",
                balance=Decimal("0.00"),
                currency="USD",
                status=AccountStatus.active,
                account_type=AccountType.airline,
            ),
            Account(
                id=settings.insurer_account_id,
                owner_name="SafeTrip Insurance",
                balance=Decimal("0.00"),
                currency="USD",
                status=AccountStatus.active,
                account_type=AccountType.insurer,
            ),
        ]

        user_accounts = [
            Account(
                id=uuid.uuid4(),
                owner_name=name,
                balance=balance,
                currency="USD",
                status=AccountStatus.active,
                account_type=AccountType.user,
            )
            for name, balance in DUMMY_USERS
        ]

        broke_user = Account(
            id=BROKE_USER_ID,
            owner_name="Broke User",
            balance=Decimal("0.00"),
            currency="USD",
            status=AccountStatus.active,
            account_type=AccountType.user,
        )

        session.add_all(system_accounts + [user_1, broke_user] + user_accounts)

        await session.commit()

        print("\n=== SYSTEM ACCOUNTS ===")
        print(f"Airline  : {settings.airline_account_id}  — SkyWings Airlines")
        print(f"Insurer  : {settings.insurer_account_id}  — SafeTrip Insurance")
        print("\n=== USER ACCOUNTS ===")
        print(f"{user_1.id}  — {'User 1':<20} balance: ${user_1.balance}")
        print(f"{broke_user.id}  — {'Broke User':<20} balance: ${broke_user.balance}")
        for acc in user_accounts:
            print(f"{acc.id}  — {acc.owner_name:<20} balance: ${acc.balance}")


if __name__ == "__main__":
    asyncio.run(seed())
