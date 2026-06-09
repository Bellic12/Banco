from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from banco.db.base import get_db
from banco.config import settings
from banco.transactions.repository import TransactionRepository
from banco.transactions.schema import PaymentRequest, PaymentResponse, TransactionResponse, TransactionListResponse
from banco.transactions.service import PaymentService

router = APIRouter(prefix="/api/v1")


@router.post("/payments", response_model=PaymentResponse, status_code=201)
async def pay(request: PaymentRequest, db: AsyncSession = Depends(get_db)):
    service = PaymentService(db)
    return await service.pay(request, settings.airline_account_id, settings.insurer_account_id)


@router.get("/transactions/{transaction_id}", response_model=TransactionResponse)
async def get_transaction(transaction_id: UUID, db: AsyncSession = Depends(get_db)):
    repo = TransactionRepository(db)
    transaction = await repo.get_by_id(transaction_id)
    if not transaction:
        raise HTTPException(status_code=404, detail={"error": "TRANSACTION_NOT_FOUND", "message": f"Transaction {transaction_id} not found"})
    return transaction


@router.get("/transactions", response_model=TransactionListResponse)
async def get_transactions_by_reference(reference: str, db: AsyncSession = Depends(get_db)):
    repo = TransactionRepository(db)
    transactions = await repo.get_by_reference(reference)
    return TransactionListResponse(reference=reference, transactions=transactions)
