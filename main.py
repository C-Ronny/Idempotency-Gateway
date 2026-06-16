from fastapi import FastAPI, Header, Response
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
async def process_payment(body: PaymentRequest, response: Response, idempotency_key: str = Header(...)):
    
    # US1: The First Transaction (Happy Path)
    if idempotency_key not in idempotency_store: # Check if the key exists in the store
        
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
    
    # US2: The Duplicate Attempt (Idempotency Logic)
    else:        
        # assigns key to stored if it exists
        stored = idempotency_store[idempotency_key] 

        # if the incoming request is the same as the stored one
        if stored["request"] == body.model_dump():
            # Indicate it was a replayed response
            response.headers["X-Cache-Hit"] = "true"
            return stored["response"]

