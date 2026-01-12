# Exercise Tracker

A comprehensive list of all exercises in this MLOps FastAPI lab, organized by phase.

---

## Phase 1: Foundation (Completed ✅)

**Learning Objective:** Understand the basics of FastAPI, async/sync patterns, and why concurrency matters for ML inference services.

### Step 0: Environment Setup ✅
- [x] Install `uv` package manager
- [x] Initialize project with `uv init`
- [x] Add dependencies: `fastapi`, `uvicorn[standard]`
- [x] Create `app/` directory structure

### Exercise 1: First FastAPI Inference Endpoint ✅
- [x] **1.1** Create `app/main.py` with FastAPI app and `/health` endpoint
- [x] **1.2** Create `app/schemas.py` with Pydantic models (`PredictRequest`, `PredictResponse`)
- [x] **1.3** Create `/predict` endpoint with simulated latency
- [x] **1.4** Run concurrent request experiment - observe blocking behavior
- [x] **1.5** Fix with `async def` + `asyncio.sleep()`
- [x] **1.6** Understand the difference between sync/async patterns
- [x] **1.7** Create comparison endpoints (`/predict/sync`, `/predict/async`, `/predict/broken`)

**Key Takeaways:**
- `def` + `time.sleep()` → runs in thread pool (concurrent)
- `async def` + `await asyncio.sleep()` → runs on event loop (concurrent)
- `async def` + `time.sleep()` → BROKEN, blocks event loop (sequential)

---

## Phase 1.5: Sync vs Async Mastery (Complete ✅)

**Learning Objective:** Build deep intuition for when to use `def`, `async def`, threads, or workers through hands-on practice across diverse real-world scenarios.

### Sync/Async Practice Exercises
See `docs/Exercises/sync-async-exercises.md` for full details.

- [x] **A** Database Lookup (blocking driver) - `psycopg2` style ✅
- [x] **B** External API Call (async HTTP client) - `httpx` style ✅
- [x] **C** CPU-Heavy Computation - hashing, ML inference ✅
- [x] **D** File Read (blocking I/O) - standard `open()` ✅
- [x] **E** Cache Lookup (async Redis) - high-throughput cache ✅
- [x] **F** Mixed Workload - ML preprocessing + inference ✅
- [x] **G** Fire-and-Forget Logging - background tasks ✅
- [x] **H** Batch Parallel Requests - `asyncio.gather()` ✅

**Key Concepts:**
- Match the pattern to the library's capabilities
- Blocking library + `async def` = disaster
- CPU-bound needs workers, not async
- `asyncio.gather()` for parallel I/O
- `BackgroundTasks` for fire-and-forget

**Scoring:**
| Correct | Level |
|---------|-------|
| 8/8 | Expert - ready for production MLOps |
| 6-7/8 | Solid - review the ones you missed |
| 4-5/8 | Getting there - re-read the docs |
| <4/8 | Review threading-fundamentals.md |

---

## Phase 2: Observability (In Progress 🔄)

**Learning Objective:** Learn to instrument your service for production monitoring - measure latency, calculate percentiles, and expose metrics.

### Exercise 2: Adding Timing Middleware 🔄
- [x] **2.1** Create `app/middleware.py` with middleware skeleton
- [x] **2.2** Understand middleware structure (before/after request pattern)
- [x] **2.3** Capture request timing with `time.perf_counter()`
- [x] **2.7** Register middleware in `main.py` (done early)
- [ ] **2.4** Store latency samples (keep last N measurements in memory)
- [ ] **2.5** Calculate percentiles (p50, p95, p99)
- [ ] **2.6** Create `/metrics` endpoint to expose collected data

**Key Concepts:**
- Middleware intercepts all requests without modifying endpoints
- Percentiles (p50, p95, p99) reveal more than averages
- Observability is essential for production debugging

---

## Phase 3: Load Testing (Pending 📋)

**Learning Objective:** Learn to simulate real-world traffic, find breaking points, and understand service behavior under stress.

### Exercise 3: Load Testing with Locust
- [ ] **3.1** Install Locust (`uv add locust`)
- [ ] **3.2** Create `locustfile.py` with user behavior simulation
- [ ] **3.3** Run Locust web UI and execute load tests
- [ ] **3.4** Analyze results: requests/second, response times, failure rates
- [ ] **3.5** Find the breaking point of your service
- [ ] **3.6** Compare load test results across `/predict/sync`, `/predict/async`, `/predict/broken`

**Key Concepts:**
- Load testing reveals issues that single-request testing misses
- Understand throughput vs latency tradeoffs
- Identify bottlenecks before production

---

## Phase 4: Performance Tuning (Pending 📋)

**Learning Objective:** Learn to tune FastAPI/uvicorn for production workloads - worker processes, connection limits, and resource management.

### Exercise 4: Tuning for Throughput
- [ ] **4.1** Experiment with `--workers N` (multiple uvicorn processes)
- [ ] **4.2** Understand worker count vs CPU cores relationship
- [ ] **4.3** Measure throughput improvement with multiple workers
- [ ] **4.4** Understand memory implications (each worker loads full app)
- [ ] **4.5** Learn when to use workers vs async vs both
- [ ] **4.6** Configure for CPU-bound vs I/O-bound workloads

**Key Concepts:**
- Workers = processes = bypass GIL for true parallelism
- Worker count should match CPU cores for CPU-bound work
- Memory usage scales with worker count

---

## Phase 5: Containerization (Pending 📋)

**Learning Objective:** Package your service for deployment using Docker - the standard for production ML services.

### Exercise 5: Dockerizing the Service
- [ ] **5.1** Create `Dockerfile` for the FastAPI app
- [ ] **5.2** Understand multi-stage builds for smaller images
- [ ] **5.3** Create `docker-compose.yml` for easy local development
- [ ] **5.4** Configure uvicorn for container environment
- [ ] **5.5** Add health checks for container orchestration
- [ ] **5.6** Run load tests against containerized service

**Key Concepts:**
- Containers provide consistent deployment environments
- Multi-stage builds reduce image size
- Health checks enable orchestrator integration (Kubernetes)

---

## Progress Summary

| Phase | Topic | Status |
|-------|-------|--------|
| 1 | Foundation (FastAPI, async/sync) | ✅ Complete |
| 1.5 | Sync vs Async Mastery (8 exercises) | ✅ Complete |
| 2 | Observability (middleware, metrics) | 🔄 In Progress |
| 3 | Load Testing (Locust) | 📋 Pending |
| 4 | Performance Tuning (workers) | 📋 Pending |
| 5 | Containerization (Docker) | 📋 Pending |

---

## Documentation Created

| File | Topic |
|------|-------|
| `docs/Learning/concurrency-and-parallelism.md` | Deep dive into async, threading, and how it relates to Kubernetes scaling |
| `docs/Learning/threading-fundamentals.md` | Ground-up explanation of processes, threads, GIL, and thread pools |
| `docs/Exercises/exercise-tracker.md` | This file - exercise progress tracking |
| `docs/Exercises/sync-async-exercises.md` | 8 hands-on exercises for sync/async mastery |

---

## Next Step

**Option 1:** Work through **Phase 1.5 exercises** (A-H) in `sync-async-exercises.md` to build mastery.

**Option 2:** Continue with **Exercise 2.4**: Store latency samples in memory for percentile calculations.
