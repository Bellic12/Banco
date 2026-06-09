import asyncio
from uuid import UUID
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from banco.users.repository import AccountRepository
from banco.users.models import AccountStatus
from banco.transactions.repository import TransactionRepository
from banco.transactions.models import Transaction, TransactionType, TransactionStatus
from banco.transactions.schema import PaymentRequest, PaymentResponse
from banco.callbacks import notify_airline
from fastapi import HTTPException


class PaymentService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.account_repo = AccountRepository(db)
        self.transaction_repo = TransactionRepository(db)

    async def _record(
        self,
        from_account_id: UUID,
        to_account_id: UUID,
        amount: Decimal,
        transaction_type: TransactionType,
        status: TransactionStatus,
    ) -> None:
        await self.transaction_repo.create(Transaction(
            type=transaction_type,
            status=status,
            amount=amount,
            currency="USD",
            from_account_id=from_account_id,
            to_account_id=to_account_id,
            reference="",
        ))

    async def pay(
        self,
        request: PaymentRequest,
        airline_account_id: UUID,
        insurer_account_id: UUID,
        callback_url: str,
    ) -> PaymentResponse:
        user_account = await self.account_repo.get_by_id(request.user_account_id)
        if not user_account:
            raise HTTPException(status_code=404, detail={"error": "ACCOUNT_NOT_FOUND", "message": f"Account {request.user_account_id} not found"})

        if user_account.status != AccountStatus.active:
            raise HTTPException(status_code=400, detail={"error": "ACCOUNT_INACTIVE", "message": "User account is inactive"})

        total = request.flight_amount + request.insurance_amount
        if user_account.balance < total:
            raise HTTPException(
                status_code=400,
                detail={"error": "INSUFFICIENT_FUNDS", "message": f"Account balance {user_account.balance} is less than required {total}"},
            )

        airline_account = await self.account_repo.get_by_id(airline_account_id)
        await self.account_repo.debit(user_account, request.flight_amount)
        await self.account_repo.credit(airline_account, request.flight_amount)
        await self._record(request.user_account_id, airline_account_id, request.flight_amount, TransactionType.flight, TransactionStatus.success)

        if request.insurance_amount > 0:
            insurer_account = await self.account_repo.get_by_id(insurer_account_id)
            await self.account_repo.debit(user_account, request.insurance_amount)
            await self.account_repo.credit(insurer_account, request.insurance_amount)
            await self._record(request.user_account_id, insurer_account_id, request.insurance_amount, TransactionType.insurance, TransactionStatus.success)

        await self.db.commit()
        if callback_url:
            asyncio.create_task(notify_airline(callback_url, True, str(request.user_account_id)))
        return PaymentResponse(success=True)
