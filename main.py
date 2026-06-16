from fastapi import FastAPI, Header
from pydantic import BaseModel
import asyncio

class PaymentRequest(BaseModel):
    amount: float
    currency: str

app = FastAPI()

# Store for HTTP header value and response body
idempotency_store ={}


@app.get("/")
def read_root():
    return {"status": "ok"}


@app.post("/process-payment")
async def process_payment(body: PaymentRequest, idempotency_key: str = Header(...)):
    # Check if the key exists in the store
    if idempotency_key not in idempotency_store:
        # US1: Happy Path
        await asyncio.sleep(2)  # Simulate the 2-second processing delay

        amount = body.amount
        if amount == int(amount):       # Check if it's a whole number
            amount_str = int(amount)    # 100.0 -> 100
        else:
            amount_str = amount         # 100.50 -> 100.50
        
        response_body = {"message": f"Charged {amount_str} {body.currency}"}

        # Save key -> {request, response} so future duplicates can be detected/replayed
        idempotency_store[idempotency_key] = {
            "request": body.model_dump(),
            "response": response_body,
        }
        return response_body