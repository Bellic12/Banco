from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from banco.db.base import get_db
from banco.config import settings
from banco.users.repository import AccountRepository
from banco.users.schema import AccountResponse
from banco.transactions.repository import TransactionRepository
from banco.transactions.schema import PaymentRequest, TransactionResponse, TransactionListResponse
from banco.transactions.service import PaymentService

router = APIRouter(prefix="/api/v1")


@router.get("/accounts/{account_id}", response_model=AccountResponse)
async def get_account(account_id: UUID, db: AsyncSession = Depends(get_db)):
    repo = AccountRepository(db)
    account = await repo.get_by_id(account_id)
    if not account:
        raise HTTPException(status_code=404, detail={"error": "ACCOUNT_NOT_FOUND", "message": f"Account {account_id} not found"})
    return account


@router.post("/payments/flight", response_model=TransactionResponse, status_code=201)
async def pay_flight(request: PaymentRequest, db: AsyncSession = Depends(get_db)):
    service = PaymentService(db)
    transaction = await service.pay_flight(request, settings.airline_account_id)
    return transaction


@router.post("/payments/insurance", response_model=TransactionResponse, status_code=201)
async def pay_insurance(request: PaymentRequest, db: AsyncSession = Depends(get_db)):
    service = PaymentService(db)
    transaction = await service.pay_insurance(request, settings.insurer_account_id)
    return transaction


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
