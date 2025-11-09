# REST API Assignment

This project implements a production-style REST API using FastAPI. The service simulates a small warehouse operation and exposes ten endpoints across the common HTTP CRUD verbs:

- GET: `/inventory`, `/orders/{order_id}`
- POST: `/inventory`, `/orders`
- PUT: `/inventory/{item_id}`, `/orders/{order_id}`
- PATCH: `/inventory/{item_id}`, `/orders/{order_id}`
- DELETE: `/inventory/{item_id}`, `/orders/{order_id}`

The API keeps data in memory for simplicity while demonstrating request validation, error handling, and partial updates.

## Prerequisites

- Python 3.10+
- Recommended: virtual environment such as `venv` or `conda`

## Setup

```powershell
cd c:\Users\Jonco\OneDrive\Documents\GitHub\REST-API-Assignment
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -r requirements.txt
```

## Run the API

```powershell
uvicorn app.main:app --reload
```

The server listens on `http://127.0.0.1:8000`. Open `http://127.0.0.1:8000/docs` for auto-generated Swagger UI.

## Example Requests

```powershell
# Create an inventory item
curl -X POST http://127.0.0.1:8000/inventory ^
	-H "Content-Type: application/json" ^
	-d '{"name":"Widget","quantity":10,"price":12.5}'

# Create an order referencing the item with id 1
curl -X POST http://127.0.0.1:8000/orders ^
	-H "Content-Type: application/json" ^
	-d '{"customer":"Ada Lovelace","items":[1],"status":"pending"}'

# Fetch the newly created order
curl http://127.0.0.1:8000/orders/1
```

## Tests

```powershell
pytest
```

The test suite exercises all endpoints end-to-end via FastAPI's `TestClient`.

## Recording Submission

After running the curl or Postman demonstrations, capture a short screen recording that shows:

1. The server running locally.
2. Requests being made to each endpoint (curl/Postman).
3. The responses returned by the API.

Include the recording along with this source code when submitting Assignment 10.