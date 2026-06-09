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

### POST `/payments`

Single endpoint for all payments. Atomically debits the user and credits the airline (always) and insurer (if `insurance_amount` > 0). Balance is checked against the total before any money moves.

**Called by:** Airline system — once booking is confirmed

**Request**
```json
{
  "user_account_id": "700c6f46-e427-40d7-87f0-6b7c76ada214",
  "flight_amount": 350.00,
  "insurance_amount": 45.00,
  "currency": "USD",
  "reference": "FLIGHT-REF-001"
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| `user_account_id` | UUID | yes | Paying user's account |
| `flight_amount` | Decimal | yes | Amount to transfer to airline (must be > 0) |
| `insurance_amount` | Decimal | no | Amount to transfer to insurer (default `0.00`, omit if no insurance) |
| `currency` | String | no | 3-letter currency code, default `USD` (must match account currency) |
| `reference` | String | yes | Booking reference from airline system |

**Response `201` — flight only**
```json
{
  "reference": "FLIGHT-REF-001",
  "total_debited": 350.00,
  "currency": "USD",
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
    }
  ]
}
```

**Response `201` — flight + insurance**
```json
{
  "reference": "FLIGHT-REF-001",
  "total_debited": 395.00,
  "currency": "USD",
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
      "timestamp": "2026-06-09T14:30:00Z"
    }
  ]
}
```

**Error cases**

| Status | Error Code | Cause |
|---|---|---|
| `404` | `ACCOUNT_NOT_FOUND` | User account ID does not exist |
| `400` | `ACCOUNT_INACTIVE` | User account is inactive |
| `400` | `INSUFFICIENT_FUNDS` | Balance < `flight_amount + insurance_amount` |
| `400` | `CURRENCY_MISMATCH` | Request currency does not match account currency |
| `422` | *(validation)* | `flight_amount` ≤ 0, `insurance_amount` < 0, or missing required fields |

> If validation or balance check fails, **no money moves** — the entire operation is aborted before any debit occurs.

---

### GET `/transactions/{transaction_id}`

Fetch a single transaction by ID.

**Called by:** Airline system — to confirm a specific transfer

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

**Called by:** Airline system or Insurance system — to audit all payments for a booking

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
      "timestamp": "2026-06-09T14:30:00Z"
    }
  ]
}
```

Returns empty `transactions` array if reference not found (not a 404).

---

## Integration Flow

```
Airline System
  1. POST /payments   { flight_amount, insurance_amount (optional), user_account_id, reference }
  2. On 201 → booking confirmed, store transaction IDs
  3. On 400 INSUFFICIENT_FUNDS → notify user, abort booking
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
| `INSUFFICIENT_FUNDS` | 400 | Balance < total required amount |
| `CURRENCY_MISMATCH` | 400 | Request currency ≠ account currency |
| `INVALID_AMOUNT` | 422 | `flight_amount` ≤ 0 or `insurance_amount` < 0 |
| `TRANSACTION_NOT_FOUND` | 404 | No transaction with that ID |
| `INTERNAL_ERROR` | 500 | Unexpected server error |
