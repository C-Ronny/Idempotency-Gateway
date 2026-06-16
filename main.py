from fastapi import FastAPI, Header, Response, HTTPException
from pydantic import BaseModel
import asyncio
import time


IDEMPOTENCY_TTL_SECONDS = 86400  # 24 hours

class PaymentRequest(BaseModel):
    amount: float
    currency: str

app = FastAPI()

# Store for HTTP header value and response body
idempotency_store ={}

# dict to store locks
locks = {}


@app.get("/")
def read_root():
    return {"status": "ok"}


@app.post("/process-payment")
async def process_payment(body: PaymentRequest, response: Response, idempotency_key: str = Header(...)):

    if idempotency_key not in locks:
        locks[idempotency_key] = asyncio.Lock()

    async with locks[idempotency_key]:

        is_new = idempotency_key not in idempotency_store
        is_expired = (
            not is_new
            and time.time() - idempotency_store[idempotency_key]["timestamp"] > IDEMPOTENCY_TTL_SECONDS
        )

        # US1: The First Transaction (Happy Path)
        if is_new or is_expired: 
            
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
                "timestamp": time.time(),
            }
            return response_body
        
        else:        
            # assigns key to stored if it exists
            stored = idempotency_store[idempotency_key] 

            # US2: The Duplicate Attempt (Idempotency Logic)        
            if stored["request"] == body.model_dump(): # incoming request == stored one
                # Indicate it was a replayed response
                response.headers["X-Cache-Hit"] = "true"
                return stored["response"]

            # US3: Different Request, Same Key (Fraud/Error Check)        
            raise HTTPException(
                status_code=422, 
                detail="Idempotency key already used for a different request body."
            )