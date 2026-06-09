from uuid import UUID
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from banco.users.repository import AccountRepository
from banco.users.models import AccountStatus
from banco.transactions.repository import TransactionRepository
from banco.transactions.models import Transaction, TransactionType, TransactionStatus
from banco.transactions.schema import PaymentRequest, PaymentResponse
from fastapi import HTTPException


class PaymentService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.account_repo = AccountRepository(db)
        self.transaction_repo = TransactionRepository(db)

    async def _build_transaction(
        self,
        from_account_id: UUID,
        to_account_id: UUID,
        amount: Decimal,
        currency: str,
        reference: str,
        transaction_type: TransactionType,
    ) -> Transaction:
        transaction = Transaction(
            type=transaction_type,
            status=TransactionStatus.pending,
            amount=amount,
            currency=currency,
            from_account_id=from_account_id,
            to_account_id=to_account_id,
            reference=reference,
        )
        await self.transaction_repo.create(transaction)
        return transaction

    async def pay(
        self,
        request: PaymentRequest,
        airline_account_id: UUID,
        insurer_account_id: UUID,
    ) -> PaymentResponse:
        user_account = await self.account_repo.get_by_id(request.user_account_id)
        if not user_account:
            raise HTTPException(status_code=404, detail={"error": "ACCOUNT_NOT_FOUND", "message": f"Account {request.user_account_id} not found"})

        if user_account.status != AccountStatus.active:
            raise HTTPException(status_code=400, detail={"error": "ACCOUNT_INACTIVE", "message": "User account is inactive"})

        if user_account.currency != request.currency:
            raise HTTPException(status_code=400, detail={"error": "CURRENCY_MISMATCH", "message": f"Account currency {user_account.currency} does not match {request.currency}"})

        total = request.flight_amount + request.insurance_amount
        if user_account.balance < total:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "INSUFFICIENT_FUNDS",
                    "message": f"Account balance {user_account.balance} is less than required {total}",
                },
            )

        airline_account = await self.account_repo.get_by_id(airline_account_id)
        transactions = []

        flight_tx = await self._build_transaction(
            from_account_id=request.user_account_id,
            to_account_id=airline_account_id,
            amount=request.flight_amount,
            currency=request.currency,
            reference=request.reference,
            transaction_type=TransactionType.flight,
        )
        await self.account_repo.debit(user_account, request.flight_amount)
        await self.account_repo.credit(airline_account, request.flight_amount)
        flight_tx.status = TransactionStatus.success
        transactions.append(flight_tx)

        if request.insurance_amount > 0:
            insurer_account = await self.account_repo.get_by_id(insurer_account_id)
            insurance_tx = await self._build_transaction(
                from_account_id=request.user_account_id,
                to_account_id=insurer_account_id,
                amount=request.insurance_amount,
                currency=request.currency,
                reference=request.reference,
                transaction_type=TransactionType.insurance,
            )
            await self.account_repo.debit(user_account, request.insurance_amount)
            await self.account_repo.credit(insurer_account, request.insurance_amount)
            insurance_tx.status = TransactionStatus.success
            transactions.append(insurance_tx)

        await self.db.commit()
        for tx in transactions:
            await self.db.refresh(tx)

        return PaymentResponse(
            reference=request.reference,
            total_debited=total,
            currency=request.currency,
            transactions=transactions,
        )
