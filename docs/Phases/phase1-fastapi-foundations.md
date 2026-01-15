# FastAPI Foundations for MLOps

Notes from Phase 1 - building your first ML inference API with FastAPI.

---

## Why FastAPI for ML Inference?

| Feature | Benefit for ML |
|---------|----------------|
| Async support | Handle many concurrent prediction requests |
| Pydantic validation | Automatic input validation for model features |
| Auto-generated docs | OpenAPI/Swagger for API consumers |
| Type hints | Clear contracts for request/response schemas |
| Performance | One of the fastest Python frameworks |

---

## Project Structure

```
app/
├── main.py          # FastAPI app, routes, middleware registration
├── schemas.py       # Pydantic models for request/response
├── middleware.py    # Cross-cutting concerns (timing, logging)
└── routers/         # Route modules for organization
    └── exercises.py
```

---

## Pydantic Models for ML

### Request Schema

```python
from pydantic import BaseModel

class PredictRequest(BaseModel):
    feature_1: float
    feature_2: float
```

**Benefits:**
- Automatic type validation
- Clear documentation in Swagger UI
- IDE autocomplete support

### Response Schema

```python
class PredictResponse(BaseModel):
    prediction: float
    model_version: str
```

**Best practice:** Always include `model_version` in responses for debugging and reproducibility.

---

## The Critical Async/Sync Decision

This is the most important concept for ML inference APIs.

### The Three Patterns

| Pattern | Code | Behavior |
|---------|------|----------|
| Sync function | `def` + `time.sleep()` | Runs in thread pool (concurrent) |
| Async function | `async def` + `await asyncio.sleep()` | Runs on event loop (concurrent) |
| **BROKEN** | `async def` + `time.sleep()` | Blocks event loop (sequential!) |

### Why This Matters for ML

Real ML inference often involves:
- **I/O-bound**: Loading models from disk, calling external APIs
- **CPU-bound**: Running model inference (matrix operations)

| Workload | Correct Pattern |
|----------|-----------------|
| Async I/O (httpx, aiofiles) | `async def` + `await` |
| Blocking I/O (requests, open()) | `def` (thread pool) |
| CPU-heavy (model inference) | `def` + multiple workers |

### The Broken Pattern Explained

```python
# BROKEN - blocks the entire event loop!
@app.post("/predict")
async def predict():
    time.sleep(0.1)  # Blocking call in async function
    return {"prediction": 0.5}
```

When you use `async def`, FastAPI runs your function on the event loop. If you block with `time.sleep()`, **no other requests can be processed** until it completes.

**Fix options:**
1. Use `await asyncio.sleep()` for async delays
2. Use `def` instead of `async def` for blocking operations
3. Use `run_in_executor()` to offload blocking code

---

## FastAPI App Setup

### Basic App

```python
from fastapi import FastAPI

app = FastAPI(
    title="MLOps Inference API",
    description="FastAPI service for ML inference",
    version="1.0.0"
)
```

### Health Check Endpoint

Every production service needs a health check:

```python
@app.get("/health")
def health_check():
    return {"status": "healthy"}
```

Used by:
- Load balancers (routing traffic)
- Kubernetes (liveness/readiness probes)
- Monitoring systems (uptime tracking)

### Prediction Endpoint

```python
@app.post("/predict", response_model=PredictResponse)
async def predict(request: PredictRequest):
    # Simulate inference latency
    await asyncio.sleep(0.1)

    prediction = model.predict(request.feature_1, request.feature_2)
    return PredictResponse(
        prediction=prediction,
        model_version="1.0.0"
    )
```

---

## Running the Server

### Development

```bash
# With FastAPI CLI (includes auto-reload)
uv run fastapi dev app/main.py

# With uvicorn directly
uv run uvicorn app.main:app --reload
```

### Production

```bash
# Multiple workers for CPU-bound workloads
uv run uvicorn app.main:app --workers 4
```

---

## Testing Concurrent Requests

### Using curl in a loop

```bash
# Generate multiple requests
for i in {1..100}; do
  curl -s http://localhost:8000/health > /dev/null
done
```

### Observing the difference

With the **broken pattern** (`async def` + `time.sleep`):
- 10 requests with 100ms delay = 1000ms total (sequential)

With the **correct pattern**:
- 10 requests with 100ms delay = ~100ms total (concurrent)

---

## Key Takeaways

1. **Choose async/sync deliberately** - match your pattern to the library's capabilities
2. **Never block the event loop** - `async def` + blocking call = disaster
3. **Use Pydantic** for automatic validation and documentation
4. **Always have /health** - it's required for production deployments
5. **Include model_version** in responses for debugging
6. **Test with concurrent requests** - single-request testing hides concurrency bugs

---

## Phase 1 Complete!

- [x] Create FastAPI app with health endpoint
- [x] Create Pydantic schemas for ML requests/responses
- [x] Implement /predict endpoint with simulated latency
- [x] Understand sync vs async patterns
- [x] Identify and fix the "broken" async pattern
- [x] Create comparison endpoints for experimentation

---

## Related Documentation

- `threading-fundamentals.md` - Deep dive into threads, GIL, and thread pools
- `concurrency-and-parallelism.md` - How this relates to Kubernetes scaling
- `latency-monitoring.md` - Phase 2: Adding observability
