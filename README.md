# Banco — Banking System

Internal banking service for the flight ticket purchasing platform. Handles money transfers between user accounts and system accounts (airline, insurer).

## System Accounts

These IDs are fixed and environment-configured. All other systems must use them as destination targets.

| Role | Name | Account ID |
|---|---|---|
| Airline | SkyWings Airlines | `00000000-0000-0000-0000-000000000001` |
| Insurer | SafeTrip Insurance | `00000000-0000-0000-0000-000000000002` |

---

## Running

```bash
docker compose up --build
```

API available at `http://localhost:8000`
Interactive docs at `http://localhost:8000/docs`

> DB is wiped and re-seeded with fresh dummy users on every startup.

---

## API Reference

Base URL: `http://localhost:8000/api/v1`

All responses use JSON. All error responses follow the format:

```json
{
  "error": "ERROR_CODE",
  "message": "Human-readable description"
}
```

---

### GET `/accounts/{account_id}`

Fetch account info and current balance.

**Called by:** Airline system (to verify user has funds before initiating payment)

**Request**
```
GET /api/v1/accounts/700c6f46-e427-40d7-87f0-6b7c76ada214
```

**Response `200`**
```json
{
  "id": "700c6f46-e427-40d7-87f0-6b7c76ada214",
  "owner_name": "Alice Johnson",
  "balance": 8500.00,
  "currency": "USD",
  "status": "active",
  "account_type": "user"
}
```

**Error cases**

| Status | Error Code | Cause |
|---|---|---|
| `404` | `ACCOUNT_NOT_FOUND` | Account ID does not exist |

---

### POST `/payments/flight`

Debit user account and credit airline account.

**Called by:** Airline system — after confirming flight booking

**Request**
```json
{
  "user_account_id": "700c6f46-e427-40d7-87f0-6b7c76ada214",
  "amount": 350.00,
  "currency": "USD",
  "reference": "FLIGHT-REF-001"
}
```

| Field | Type | Description |
|---|---|---|
| `user_account_id` | UUID | Paying user's account |
| `amount` | Decimal | Amount to transfer (must be > 0) |
| `currency` | String | 3-letter currency code (must match account currency) |
| `reference` | String | Flight booking reference from airline system |

**Response `201`**
```json
{
  "id": "a3f1c2d4-...",
  "type": "flight",
  "status": "SUCCESS",
  "amount": 350.00,
  "currency": "USD",
  "from_account_id": "700c6f46-e427-40d7-87f0-6b7c76ada214",
  "to_account_id": "00000000-0000-0000-0000-000000000001",
  "reference": "FLIGHT-REF-001",
  "failure_reason": null,
  "timestamp": "2026-06-09T14:30:00Z"
}
```

**Error cases**

| Status | Error Code | Cause |
|---|---|---|
| `404` | `ACCOUNT_NOT_FOUND` | User account ID does not exist |
| `400` | `ACCOUNT_INACTIVE` | User account is inactive |
| `400` | `INSUFFICIENT_FUNDS` | User balance is less than requested amount |
| `400` | `CURRENCY_MISMATCH` | Request currency does not match account currency |
| `422` | *(validation)* | `amount` ≤ 0 or missing required fields |

---

### POST `/payments/insurance`

Debit user account and credit insurer account.

**Called by:** Airline system — only when user opted in to insurance during booking

**Request**
```json
{
  "user_account_id": "700c6f46-e427-40d7-87f0-6b7c76ada214",
  "amount": 45.00,
  "currency": "USD",
  "reference": "FLIGHT-REF-001"
}
```

Same fields as `/payments/flight`. Use the **same `reference`** as the flight payment to link both transactions.

**Response `201`**
```json
{
  "id": "b7e2a1f9-...",
  "type": "insurance",
  "status": "SUCCESS",
  "amount": 45.00,
  "currency": "USD",
  "from_account_id": "700c6f46-e427-40d7-87f0-6b7c76ada214",
  "to_account_id": "00000000-0000-0000-0000-000000000002",
  "reference": "FLIGHT-REF-001",
  "failure_reason": null,
  "timestamp": "2026-06-09T14:31:00Z"
}
```

**Error cases** — identical to `/payments/flight`

---

### GET `/transactions/{transaction_id}`

Fetch a single transaction by ID.

**Called by:** Airline system — to confirm payment status after calling a payment endpoint

**Request**
```
GET /api/v1/transactions/a3f1c2d4-...
```

**Response `200`**
```json
{
  "id": "a3f1c2d4-...",
  "type": "flight",
  "status": "SUCCESS",
  "amount": 350.00,
  "currency": "USD",
  "from_account_id": "700c6f46-...",
  "to_account_id": "00000000-0000-0000-0000-000000000001",
  "reference": "FLIGHT-REF-001",
  "failure_reason": null,
  "timestamp": "2026-06-09T14:30:00Z"
}
```

**Error cases**

| Status | Error Code | Cause |
|---|---|---|
| `404` | `TRANSACTION_NOT_FOUND` | Transaction ID does not exist |

---

### GET `/transactions?reference={reference}`

Fetch all transactions tied to a booking reference.

**Called by:** Airline system or Insurance system — to audit all payments for a given booking

**Request**
```
GET /api/v1/transactions?reference=FLIGHT-REF-001
```

**Response `200`**
```json
{
  "reference": "FLIGHT-REF-001",
  "transactions": [
    {
      "id": "a3f1c2d4-...",
      "type": "flight",
      "status": "SUCCESS",
      "amount": 350.00,
      "currency": "USD",
      "from_account_id": "700c6f46-...",
      "to_account_id": "00000000-0000-0000-0000-000000000001",
      "reference": "FLIGHT-REF-001",
      "failure_reason": null,
      "timestamp": "2026-06-09T14:30:00Z"
    },
    {
      "id": "b7e2a1f9-...",
      "type": "insurance",
      "status": "SUCCESS",
      "amount": 45.00,
      "currency": "USD",
      "from_account_id": "700c6f46-...",
      "to_account_id": "00000000-0000-0000-0000-000000000002",
      "reference": "FLIGHT-REF-001",
      "failure_reason": null,
      "timestamp": "2026-06-09T14:31:00Z"
    }
  ]
}
```

Returns empty `transactions` array if reference not found (not a 404).

---

## Integration Flows

### Flight only

```
Airline System
  1. GET  /accounts/{user_account_id}        → verify balance ≥ flight price
  2. POST /payments/flight                   → transfer money
  3. Store returned transaction_id
```

### Flight + Insurance

```
Airline System
  1. GET  /accounts/{user_account_id}        → verify balance ≥ flight + insurance
  2. POST /payments/flight                   → transfer flight amount
  3. POST /payments/insurance                → transfer insurance amount (same reference)
  4. Store both transaction IDs
```

> Both payments use the same `reference`. If the insurance payment fails after the flight payment succeeds, the airline system is responsible for handling that case (e.g. retry or notify user). Banco does not roll back committed transactions.

### Verify a booking's payments

```
Airline or Insurance System
  GET /transactions?reference=FLIGHT-REF-001
```

---

## Transaction Statuses

| Status | Meaning |
|---|---|
| `PENDING` | Transfer started, not yet committed |
| `SUCCESS` | Money moved, committed to DB |
| `FAILED` | Transfer failed, no money moved |

---

## Error Code Reference

| Code | HTTP | Meaning |
|---|---|---|
| `ACCOUNT_NOT_FOUND` | 404 | No account with that ID |
| `ACCOUNT_INACTIVE` | 400 | Account exists but is disabled |
| `INSUFFICIENT_FUNDS` | 400 | Balance < requested amount |
| `CURRENCY_MISMATCH` | 400 | Request currency ≠ account currency |
| `INVALID_AMOUNT` | 422 | Amount is zero or negative |
| `TRANSACTION_NOT_FOUND` | 404 | No transaction with that ID |
| `INTERNAL_ERROR` | 500 | Unexpected server error |
