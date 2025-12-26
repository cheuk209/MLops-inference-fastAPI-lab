# MLOps Inference FastAPI Lab

A hands-on learning lab for understanding **latency and throughput** in ML inference systems using FastAPI.

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
- A code editor

### Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies (we'll create requirements.txt in Exercise 1)
pip install fastapi uvicorn[standard]
```

---

## Current Exercise: Exercise 1

Let's start with Exercise 1. Your task is to create the first FastAPI endpoint.

*(Instructions will be provided interactively)*