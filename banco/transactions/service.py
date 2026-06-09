from uuid import UUID
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from banco.users.repository import AccountRepository
from banco.users.models import AccountStatus
from banco.transactions.repository import TransactionRepository
from banco.transactions.models import Transaction, TransactionType, TransactionStatus
from banco.transactions.schema import PaymentRequest, TransactionResponse
from fastapi import HTTPException


class PaymentService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.account_repo = AccountRepository(db)
        self.transaction_repo = TransactionRepository(db)

    async def _transfer(
        self,
        user_account_id: UUID,
        destination_account_id: UUID,
        amount: Decimal,
        currency: str,
        reference: str,
        transaction_type: TransactionType,
    ) -> Transaction:
        user_account = await self.account_repo.get_by_id(user_account_id)
        if not user_account:
            raise HTTPException(status_code=404, detail={"error": "ACCOUNT_NOT_FOUND", "message": f"Account {user_account_id} not found"})

        if user_account.status != AccountStatus.active:
            raise HTTPException(status_code=400, detail={"error": "ACCOUNT_INACTIVE", "message": "User account is inactive"})

        if user_account.currency != currency:
            raise HTTPException(status_code=400, detail={"error": "CURRENCY_MISMATCH", "message": f"Account currency {user_account.currency} does not match {currency}"})

        destination_account = await self.account_repo.get_by_id(destination_account_id)
        if not destination_account:
            raise HTTPException(status_code=404, detail={"error": "ACCOUNT_NOT_FOUND", "message": "Destination account not found"})

        if user_account.balance < amount:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "INSUFFICIENT_FUNDS",
                    "message": f"Account balance {user_account.balance} is less than required {amount}",
                },
            )

        transaction = Transaction(
            type=transaction_type,
            status=TransactionStatus.pending,
            amount=amount,
            currency=currency,
            from_account_id=user_account_id,
            to_account_id=destination_account_id,
            reference=reference,
        )
        await self.transaction_repo.create(transaction)

        await self.account_repo.debit(user_account, amount)
        await self.account_repo.credit(destination_account, amount)

        transaction.status = TransactionStatus.success
        await self.db.commit()
        await self.db.refresh(transaction)
        return transaction

    async def pay_flight(self, request: PaymentRequest, airline_account_id: UUID) -> Transaction:
        return await self._transfer(
            user_account_id=request.user_account_id,
            destination_account_id=airline_account_id,
            amount=request.amount,
            currency=request.currency,
            reference=request.reference,
            transaction_type=TransactionType.flight,
        )

    async def pay_insurance(self, request: PaymentRequest, insurer_account_id: UUID) -> Transaction:
        return await self._transfer(
            user_account_id=request.user_account_id,
            destination_account_id=insurer_account_id,
            amount=request.amount,
            currency=request.currency,
            reference=request.reference,
            transaction_type=TransactionType.insurance,
        )
