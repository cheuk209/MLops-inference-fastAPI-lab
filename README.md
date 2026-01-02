# MLOps Inference FastAPI Lab

A hands-on learning lab for understanding **latency, throughput, and async usages** in ML inference systems using FastAPI.

## Learning Goals

By the end of this lab, you will understand:
1. **Latency patterns** - How async vs sync affects response times
2. **Throughput limits** - Worker count, connection pooling, backpressure
3. **Profiling** - Identifying bottlenecks with timing middleware
4. **Load testing** - Simulating concurrent users, finding breaking points
5. **Docker** - Building/running inference services in containers

---

## Tech Stack (Minimal by Design)

| Component | Choice | Why |
|-----------|--------|-----|
| **API Framework** | FastAPI | Async-first, great for learning concurrency |
| **Metrics** | Built-in Python timing middleware | Zero extra deps, JSON endpoint to query |
| **Load Testing** | Locust | Python-native, web UI, single pip install |
| **ML Simulation** | Fake delays (`asyncio.sleep`) | Pure infra focus, no ML library bloat |
| **Containerization** | Docker | Realistic MLOps practice |

### Dependencies

```
fastapi
uvicorn[standard]
locust
pydantic
structlog
```

---

## Lab Structure

This lab is organized into exercises. Each exercise builds on the previous one.

### Exercise 1: Your First FastAPI Inference Endpoint
- Create a basic endpoint that simulates ML inference with a delay
- Understand the difference between `time.sleep()` and `asyncio.sleep()`
- **Goal**: See how blocking vs non-blocking affects concurrent requests

### Exercise 2: Adding Timing Middleware
- Build middleware that measures request latency
- Store and expose metrics (min, max, avg, p50, p95, p99)
- **Goal**: Learn to instrument your code for observability

### Exercise 3: Load Testing with Locust
- Write a Locust test file to simulate users
- Run load tests and observe behavior
- **Goal**: Find the breaking point of your service

### Exercise 4: Tuning for Throughput
- Experiment with uvicorn worker count
- Understand the impact of async vs sync on throughput
- **Goal**: Learn how to tune a service for production

### Exercise 5: Dockerizing the Service
- Write a Dockerfile for the inference service
- Create docker-compose for easy orchestration
- **Goal**: Package your service for deployment

---

## Getting Started

### Prerequisites
- Python 3.11+
- Docker Desktop
- [uv](https://docs.astral.sh/uv/) - Modern Python package manager
- A code editor

---

## Step 0: Environment Setup with uv

### 1. Install uv (if you haven't already)

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Or with Homebrew
brew install uv
```

### 2. Initialize the project

```bash
uv init
```

This creates `pyproject.toml` - the modern replacement for `requirements.txt`.

### 3. Add dependencies

```bash
uv add fastapi "uvicorn[standard]"
```

### 4. Create the app directory structure

```bash
mkdir app
touch app/__init__.py
```

### 5. Verify it works

```bash
uv run python -c "import fastapi; print(f'FastAPI {fastapi.__version__} installed')"
```

---

### Expected Project Structure After Step 0

```
MLops-inference-fastAPI-lab/
├── app/
│   └── __init__.py
├── pyproject.toml
├── uv.lock
├── .python-version
├── .gitignore
└── README.md
```

---

## Exercise 1: Your First FastAPI Inference Endpoint

### Learning Objectives
- Understand FastAPI application structure
- Create a POST endpoint that simulates ML inference
- Learn why request/response models matter
- Discover the critical difference between blocking and non-blocking code

---

### Step 1.1: Create the Main Application File

Create `app/main.py`. This is the entry point for your FastAPI application.

**Why `app/main.py`?**
- Convention in FastAPI projects (and Python generally)
- Keeps source code separate from config files, tests, etc.
- The `app/` directory can later hold routers, models, utils as you scale

```python
# app/main.py
from fastapi import FastAPI

app = FastAPI()


@app.get("/health")
def health_check():
    return {"status": "healthy"}
```

**Run it:**
```bash
uv run uvicorn app.main:app --reload
```

**Verify:** Open http://localhost:8000/health in your browser.

**What's happening here:**
- `app.main:app` means "in the `app/main.py` file, use the `app` object"
- `--reload` watches for file changes (dev only, never in production)

---

### Step 1.2: Create Request/Response Models

Before writing the predict endpoint, define your data contracts.

**Why models first?**
- **Type safety**: Pydantic validates input automatically
- **Documentation**: FastAPI generates OpenAPI docs from models
- **Explicit contracts**: Future you (and teammates) know exactly what's expected
- **Fail fast**: Invalid requests rejected before hitting your logic

**Bad practice (don't do this):**
```python
# Accepts anything, no validation, no documentation
@app.post("/predict")
def predict(data: dict):
    return {"prediction": 0.5}
```

**Good practice:**
```python
from pydantic import BaseModel


class PredictRequest(BaseModel):
    feature_1: float
    feature_2: float


class PredictResponse(BaseModel):
    prediction: float
    model_version: str
```

Add these models to your `app/main.py`.

---

### Step 1.3: Create the Predict Endpoint (Blocking Version)

Now add the `/predict` endpoint that simulates ML inference with a delay.

```python
import time

@app.post("/predict", response_model=PredictResponse)
def predict(request: PredictRequest):
    # Simulate ML model inference time
    time.sleep(0.1)  # 100ms delay

    return PredictResponse(
        prediction=0.85,
        model_version="1.0.0"
    )
```

**Why `time.sleep()`?**
- Simulates CPU-bound or I/O-bound work (like model inference)
- 100ms is realistic for a small ML model

**Test it:**
```bash
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"feature_1": 1.0, "feature_2": 2.0}'
```

---

### Step 1.4: Observe the Blocking Problem

This is the key learning moment. Run this experiment:

**Open two terminal windows.**

Terminal 1 - Start your server:
```bash
uv run uvicorn app.main:app --reload
```

Terminal 2 - Send 5 concurrent requests:
```bash
time (for i in {1..5}; do curl -s -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"feature_1": 1.0, "feature_2": 2.0}' & done; wait)
```

**Question for you:**
- Each request takes 0.1 seconds
- You sent 5 requests concurrently
- How long did it actually take? ~0.1s or ~0.5s?

Write down your observation before moving to 1.5.

---

### Step 1.5: The Async Solution

Now change your endpoint to use `async`:

```python
import asyncio

@app.post("/predict", response_model=PredictResponse)
async def predict(request: PredictRequest):
    # Simulate ML model inference time (non-blocking)
    await asyncio.sleep(0.1)

    return PredictResponse(
        prediction=0.85,
        model_version="1.0.0"
    )
```

**Run the same 5-request test again.** What's the total time now?

---

### Step 1.6: Understanding What Happened

| Version | `time.sleep()` | `asyncio.sleep()` |
|---------|---------------|-------------------|
| Type | Blocking | Non-blocking |
| 5 concurrent requests | ~0.5s total | ~0.1s total |
| Why? | Each request holds the thread | Requests share the event loop |

**The critical insight:**
- `time.sleep()` = Your server can only handle ONE request at a time
- `asyncio.sleep()` = Your server can handle MANY requests concurrently

**Real-world implication:**
- Blocking code → Low throughput, high latency under load
- Async code → High throughput, consistent latency

---

### Step 1.7: When to Use Sync vs Async

| Use `def` (sync) when... | Use `async def` when... |
|--------------------------|------------------------|
| Calling CPU-bound code (numpy, sklearn inference) | Waiting on I/O (database, HTTP calls, file reads) |
| Using libraries that aren't async-compatible | Using async libraries (httpx, asyncpg, aiofiles) |
| The operation is very fast (<1ms) | The operation involves waiting |

**Important:** If your ML model uses numpy/sklearn, the actual inference is CPU-bound.
We'll address this in Exercise 4 with worker processes.

---

### Exercise 1 Checklist

Before moving on, verify you have:

- [ ] `app/main.py` with FastAPI app
- [ ] `/health` endpoint (GET)
- [ ] `/predict` endpoint (POST) with async
- [ ] `PredictRequest` and `PredictResponse` Pydantic models
- [ ] Ran the concurrent request experiment and understood the difference

---

### Your Complete `app/main.py` Should Look Like:

```python
import asyncio

from fastapi import FastAPI
from pydantic import BaseModel


app = FastAPI()


class PredictRequest(BaseModel):
    feature_1: float
    feature_2: float


class PredictResponse(BaseModel):
    prediction: float
    model_version: str


@app.get("/health")
def health_check():
    return {"status": "healthy"}


@app.post("/predict", response_model=PredictResponse)
async def predict(request: PredictRequest):
    # Simulate ML model inference time (non-blocking)
    await asyncio.sleep(0.1)

    return PredictResponse(
        prediction=0.85,
        model_version="1.0.0"
    )
```

---

When you've completed Exercise 1, let me know and we'll move to **Exercise 2: Adding Timing Middleware**.