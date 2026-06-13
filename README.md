````markdown
# Idempotency-Gateway (The "Pay-Once" Protocol)

A RESTful idempotency layer that ensures each unique payment request is processed exactly once, even under client retries.

## Architecture Diagram

```mermaid
sequenceDiagram
    participant C as Client
    participant A as API
    participant S as Store

    C->>A: POST /process-payment (Idempotency-Key + body)
    A->>S: Look up Idempotency-Key

    alt Key not found (US1 - first request)
        S-->>A: Not found
        Note over A: Process payment (2s delay)
        A->>S: Save key + response
        A-->>C: 200 OK "Charged 100 GHS"
    else Key found, same body (US2 - duplicate)
        S-->>A: Found (matching body)
        A-->>C: 200 OK "Charged 100 GHS" + X-Cache-Hit: true
    else Key found, different body (US3 - conflict)
        S-->>A: Found (different body)
        A-->>C: 422 "Idempotency key already used for a different request body."
    end
```
````