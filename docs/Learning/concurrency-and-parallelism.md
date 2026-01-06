# Concurrency and Parallelism in Python & FastAPI

A deep-dive into how concurrent and parallel execution works, and how FastAPI leverages these concepts.

---

## Part 1: The Fundamental Distinction

### Concurrency vs Parallelism

These terms are often confused, but they describe different things:

| Concept | Definition | Analogy |
|---------|------------|---------|
| **Concurrency** | Managing multiple tasks that can make progress over time | One chef preparing multiple dishes, switching between them |
| **Parallelism** | Executing multiple tasks at the exact same instant | Multiple chefs each cooking a dish simultaneously |

**Key insight:** Concurrency is about *structure*. Parallelism is about *execution*.

```
Concurrency (single core, interleaved):
Task A: |██|  |██|  |██|
Task B:    |██|  |██|  |██|
Time:   ─────────────────────►

Parallelism (multiple cores, simultaneous):
Task A: |████████████|
Task B: |████████████|
Time:   ─────────────►
```

You can have concurrency without parallelism (one CPU switching between tasks), and you can have parallelism without concurrency (multiple CPUs each doing one task).

---

## Part 2: The Python Problem - The GIL

### What is the GIL?

Python has a **Global Interpreter Lock (GIL)** - a mutex that protects access to Python objects. Only one thread can execute Python bytecode at a time.

```
Thread 1: |██████|      |██████|      |██████|
Thread 2:        |██████|      |██████|
          ↑ GIL acquired by Thread 1
                 ↑ GIL released, Thread 2 acquires
```

### What This Means

| Task Type | Can benefit from threads? | Can benefit from processes? |
|-----------|--------------------------|----------------------------|
| **CPU-bound** (math, ML inference) | ❌ No - GIL blocks parallelism | ✅ Yes - each process has own GIL |
| **I/O-bound** (network, disk) | ✅ Yes - GIL released during I/O | ✅ Yes |

**This is why:**
- `threading` doesn't speed up CPU-heavy Python code
- `multiprocessing` does (separate processes, separate GILs)
- `asyncio` excels at I/O-bound workloads (no threads needed)

---

## Part 3: Three Models of Concurrency in Python

### Model 1: Threading (OS Threads)

```python
import threading
import time

def task(name):
    print(f"{name} starting")
    time.sleep(1)  # I/O simulation
    print(f"{name} done")

threads = [threading.Thread(target=task, args=(f"Thread-{i}",)) for i in range(3)]
for t in threads:
    t.start()
for t in threads:
    t.join()
```

**How it works:**
- OS manages thread scheduling
- Each thread can block independently
- GIL limits CPU parallelism, but I/O releases the GIL

**When to use:** Legacy code, simple I/O concurrency, libraries that aren't async-compatible.

---

### Model 2: Multiprocessing (OS Processes)

```python
from multiprocessing import Pool
import math

def cpu_intensive(n):
    return sum(math.sqrt(i) for i in range(n))

with Pool(4) as pool:
    results = pool.map(cpu_intensive, [10_000_000] * 4)
```

**How it works:**
- Each process has its own Python interpreter and GIL
- True parallelism on multiple CPU cores
- Higher memory overhead (processes don't share memory)

**When to use:** CPU-bound tasks like ML inference, data processing, image manipulation.

---

### Model 3: Asyncio (Cooperative Multitasking)

```python
import asyncio

async def task(name):
    print(f"{name} starting")
    await asyncio.sleep(1)  # Non-blocking I/O simulation
    print(f"{name} done")

async def main():
    await asyncio.gather(
        task("Task-1"),
        task("Task-2"),
        task("Task-3"),
    )

asyncio.run(main())
```

**How it works:**
- Single thread, single process
- Tasks voluntarily yield control at `await` points
- Event loop manages task switching
- No OS overhead for context switching

**When to use:** I/O-bound workloads (HTTP, databases, file I/O), high-concurrency servers.

---

## Part 4: The Event Loop Explained

The event loop is the heart of asyncio. Understanding it is key.

### The Mental Model

Think of the event loop as a **traffic controller** for tasks:

```
┌─────────────────────────────────────────────────────────────┐
│                       EVENT LOOP                            │
│                                                             │
│   Ready Queue          Waiting List         Running         │
│   ┌─────────┐         ┌─────────────┐      ┌─────────┐     │
│   │ Task A  │         │ Task C      │      │ Task B  │     │
│   │ Task D  │         │ (waiting on │      │executing│     │
│   │         │         │  network)   │      │         │     │
│   └─────────┘         └─────────────┘      └─────────┘     │
│        │                    │                   │           │
│        └────────────────────┴───────────────────┘           │
│                    Event Loop Cycle:                        │
│         1. Run ready tasks until they await                 │
│         2. Check if waiting tasks are ready                 │
│         3. Move ready tasks to queue                        │
│         4. Repeat                                           │
└─────────────────────────────────────────────────────────────┘
```

### What Happens at `await`

```python
async def fetch_data():
    print("Starting request")           # Runs immediately
    response = await http_client.get()  # Yields control here
    print("Got response")               # Runs when I/O completes
    return response
```

At `await`:
1. Current task is paused
2. Task is registered with the event loop to resume when I/O completes
3. Event loop runs other ready tasks
4. When I/O completes, task is marked ready and resumes

---

## Part 5: Why Blocking Code Breaks Asyncio

### The Disaster Scenario

```python
async def bad_endpoint():
    time.sleep(1)  # BLOCKING - holds the event loop hostage
    return {"status": "done"}
```

**What happens:**

```
Event Loop Timeline:
─────────────────────────────────────────────────────────►
    │
    ▼
Request 1 arrives
    │
    └──► time.sleep(1) BLOCKS
         │
         │  Event loop FROZEN
         │  Cannot process ANY other requests
         │  Request 2, 3, 4... all waiting
         │
         ▼
    (1 second later)
    Request 1 completes
    │
    └──► NOW Request 2 can start
         │
         └──► time.sleep(1) BLOCKS AGAIN...
```

**Result:** 10 requests × 1 second = 10 seconds total (sequential).

### The Correct Way

```python
async def good_endpoint():
    await asyncio.sleep(1)  # NON-BLOCKING - yields to event loop
    return {"status": "done"}
```

**What happens:**

```
Event Loop Timeline:
─────────────────────────────────────────────────────────►
    │
    ▼
Request 1, 2, 3... all arrive
    │
    └──► All call await asyncio.sleep(1)
         │
         │  All tasks registered to wake up in 1 second
         │  Event loop is FREE
         │
         ▼
    (1 second later)
    ALL requests complete simultaneously
```

**Result:** 10 requests complete in ~1 second total (parallel).

---

## Part 6: How FastAPI Handles This

FastAPI is built on **Starlette** (ASGI framework) and uses **uvicorn** (ASGI server).

### The Two Modes

#### Mode 1: `async def` (runs on event loop)

```python
@app.get("/async-endpoint")
async def async_handler():
    await some_async_io()
    return {"status": "ok"}
```

- Runs directly on the main event loop
- You MUST use `await` for any I/O
- Blocking calls freeze everything

#### Mode 2: `def` (runs in thread pool)

```python
@app.get("/sync-endpoint")
def sync_handler():
    time.sleep(1)  # Blocking, but it's OK here
    return {"status": "ok"}
```

- FastAPI automatically runs this in a thread pool
- Each request gets its own thread
- Blocking is contained to that thread
- Other requests can still be processed

### Decision Matrix

```
┌─────────────────────────────────────────────────────────────┐
│                  WHICH FUNCTION TYPE TO USE?                │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Is your code doing I/O (network, database, files)?        │
│      │                                                      │
│      ├── YES ──► Is the library async-compatible?          │
│      │               │                                      │
│      │               ├── YES ──► Use `async def` + `await` │
│      │               │                                      │
│      │               └── NO ───► Use `def` (thread pool)   │
│      │                                                      │
│      └── NO (CPU-bound) ──► Use `def` (thread pool)        │
│                             OR use background workers       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Part 7: Real-World ML Inference Implications

### The Challenge

ML inference is typically **CPU-bound**:
- Loading tensors
- Matrix multiplications
- Model forward pass

This means `asyncio` alone won't help - the GIL blocks true parallelism.

### Solutions

#### Option 1: Sync Function + Thread Pool (Simple)

```python
@app.post("/predict")
def predict(request: PredictRequest):
    result = model.predict(request.features)  # CPU-bound, blocks
    return {"prediction": result}
```

FastAPI's thread pool handles concurrency. Limited by thread count.

#### Option 2: Multiple Uvicorn Workers (Recommended for Production)

```bash
uvicorn app.main:app --workers 4
```

Each worker is a separate process with its own GIL. True parallelism.

#### Option 3: Background Task Queue (Best for Heavy Models)

```python
@app.post("/predict")
async def predict(request: PredictRequest):
    task_id = await task_queue.enqueue(model.predict, request.features)
    return {"task_id": task_id, "status": "processing"}

@app.get("/result/{task_id}")
async def get_result(task_id: str):
    result = await task_queue.get_result(task_id)
    return {"prediction": result}
```

Offload to Celery, RQ, or similar. Best for models taking >1 second.

---

## Part 8: Summary Cheat Sheet

### When to Use What

| Scenario | Approach |
|----------|----------|
| Fast I/O (HTTP calls, Redis) | `async def` + async library |
| Slow I/O (blocking database driver) | `def` (let thread pool handle it) |
| Light CPU work (<50ms) | `def` (thread pool is fine) |
| Heavy CPU work (>50ms) | Multiple workers or background queue |
| ML inference | Multiple uvicorn workers |

### Common Mistakes

| Mistake | Consequence | Fix |
|---------|-------------|-----|
| `async def` + `time.sleep()` | Freezes event loop | Use `asyncio.sleep()` |
| `async def` + blocking DB call | Freezes event loop | Use async DB driver or `def` |
| Single worker for CPU tasks | No parallelism | Use `--workers N` |
| Too many workers | Memory exhaustion | Workers ≤ CPU cores |

### The Golden Rules

1. **`async def` means "I promise to only `await`, never block"**
2. **When in doubt, use `def`** - FastAPI's thread pool is a safe default
3. **Measure under load** - single-request latency hides concurrency bugs
4. **Match workers to CPU cores** for CPU-bound workloads

---

## Part 9: Experiment Log

### Exercise 1.4-1.5 Results

| Configuration | 10 Concurrent Requests | Execution Model |
|---------------|----------------------|-----------------|
| `async def` + `time.sleep(0.1)` | ~1.1s | Sequential (broken) |
| `async def` + `asyncio.sleep(0.1)` | ~0.03s | Concurrent (correct) |
| `def` + `time.sleep(0.1)` | ~0.12s | Thread pool parallel |

These results demonstrate:
- Blocking in async functions serializes all requests
- Proper async code enables true concurrency
- Sync functions get automatic thread pool concurrency

---

## Part 10: The Full Picture - From Code to Kubernetes

As a DevOps engineer, you scale horizontally with pods. Here's how that relates to everything above.

### The Scaling Stack

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           SCALING LAYERS                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Layer 4: KUBERNETES (Horizontal Pod Scaling)                               │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐                           │
│  │   Pod 1     │ │   Pod 2     │ │   Pod 3     │  ← Separate machines/VMs  │
│  │             │ │             │ │             │     True isolation         │
│  └─────────────┘ └─────────────┘ └─────────────┘     Scale: 10s-1000s      │
│         │               │               │                                   │
│  ───────┴───────────────┴───────────────┴────────                          │
│                         │                                                   │
│  Layer 3: PROCESS (Uvicorn Workers)                                        │
│  ┌─────────────────────────────────────────────┐                           │
│  │  Pod                                        │                           │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐    │  ← Separate processes     │
│  │  │ Worker 1 │ │ Worker 2 │ │ Worker 3 │    │     Own GIL each          │
│  │  │ (CPU 1)  │ │ (CPU 2)  │ │ (CPU 3)  │    │     Scale: 1-16 per pod   │
│  │  └──────────┘ └──────────┘ └──────────┘    │                           │
│  └─────────────────────────────────────────────┘                           │
│                         │                                                   │
│  Layer 2: THREAD (FastAPI Thread Pool)                                     │
│  ┌─────────────────────────────────────────────┐                           │
│  │  Worker Process                             │                           │
│  │  ┌────────┐ ┌────────┐ ┌────────┐          │  ← OS threads             │
│  │  │Thread 1│ │Thread 2│ │Thread 3│ ...      │     Limited by GIL        │
│  │  └────────┘ └────────┘ └────────┘          │     Scale: 10-40 default  │
│  └─────────────────────────────────────────────┘                           │
│                         │                                                   │
│  Layer 1: EVENT LOOP (Asyncio)                                             │
│  ┌─────────────────────────────────────────────┐                           │
│  │  Single Thread                              │                           │
│  │  ┌──────────────────────────────────────┐  │  ← Cooperative tasks      │
│  │  │  Task A ←→ Task B ←→ Task C ←→ ...   │  │     Zero overhead         │
│  │  └──────────────────────────────────────┘  │     Scale: 1000s+ I/O ops │
│  └─────────────────────────────────────────────┘                           │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### What Each Layer Solves

| Layer | Scaling Type | Solves | Cost | Good For |
|-------|--------------|--------|------|----------|
| **Event Loop** | Concurrency (1 thread) | I/O waiting | Nearly free | HTTP calls, DB queries |
| **Thread Pool** | Concurrency (multi-thread) | Blocking I/O | Low | Sync libraries, light CPU |
| **Workers** | Parallelism (multi-process) | GIL, CPU-bound | Medium (memory) | ML inference, computation |
| **Pods** | Parallelism (multi-machine) | Single machine limits | High (infra) | Scale beyond one node |

### How They Work Together

```
Incoming Request
       │
       ▼
┌──────────────────┐
│  Load Balancer   │  ← Distributes across pods (Layer 4)
│  (K8s Service)   │
└────────┬─────────┘
         │
    ┌────┴────┐
    ▼         ▼
┌───────┐ ┌───────┐
│ Pod 1 │ │ Pod 2 │   ← Each pod runs independently
└───┬───┘ └───────┘
    │
    ▼
┌───────────────────────────────┐
│  Uvicorn with 4 workers       │  ← Distributes across workers (Layer 3)
│  (gunicorn or --workers 4)    │
└───────────────┬───────────────┘
                │
    ┌───────────┼───────────┐
    ▼           ▼           ▼
┌────────┐ ┌────────┐ ┌────────┐
│Worker 1│ │Worker 2│ │Worker 3│  ← Each worker is a process
└───┬────┘ └────────┘ └────────┘
    │
    ▼
┌────────────────────────────────┐
│  FastAPI async handler         │  ← Event loop handles I/O (Layer 1)
│  or                            │
│  FastAPI sync handler          │  ← Thread pool handles blocking (Layer 2)
└────────────────────────────────┘
```

### The Key Insight: They're Not Alternatives, They're Layers

**Common misconception:** "I have Kubernetes, so I don't need to think about async or workers."

**Reality:** Each layer multiplies the previous:

```
Total Capacity = Pods × Workers × (Threads or Async Tasks)

Example:
- 3 pods × 4 workers × 1000 concurrent async tasks = 12,000 concurrent I/O operations
- 3 pods × 4 workers × 1 sync task (no async) = 12 concurrent operations
```

If your code blocks the event loop, adding more pods just gives you more blocked event loops.

### What You Control at Each Level

| Layer | Who Controls | Configured Where |
|-------|--------------|------------------|
| Event Loop / Threads | **Developer** (you in this lab) | Python code (`async def` vs `def`) |
| Workers | **Developer / DevOps** | `uvicorn --workers N` or gunicorn |
| Pods | **DevOps** (you at work) | `kubectl`, HPA, Deployment replicas |
| Nodes | **Platform / Cloud** | Node pools, autoscaling groups |

### MLOps Scaling Strategy

For ML inference services:

```
┌─────────────────────────────────────────────────────────────────┐
│                  ML INFERENCE SCALING STRATEGY                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. START: Single pod, single worker                            │
│     - Baseline your model's latency (p50, p95, p99)            │
│     - Find single-request inference time                        │
│                                                                 │
│  2. VERTICAL: Add workers (--workers N)                         │
│     - N = number of CPU cores                                   │
│     - Watch memory! Each worker loads the model                 │
│     - Throughput scales ~linearly until CPU saturates          │
│                                                                 │
│  3. HORIZONTAL: Add pods (HPA)                                  │
│     - When single node CPU/memory maxed out                     │
│     - Scale on CPU% or custom metrics (queue depth)            │
│     - Each pod = full model copy in memory                      │
│                                                                 │
│  4. OPTIMIZE: If still not enough                               │
│     - Model optimization (ONNX, TensorRT, quantization)        │
│     - Batching requests                                         │
│     - GPU inference                                             │
│     - Model serving platforms (Triton, TF Serving)             │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Common DevOps Mistakes with Python Services

| Mistake | Why It Happens | Impact |
|---------|---------------|--------|
| HPA scaling on memory for ML | Models use constant memory | Pods never scale up |
| 1 worker per pod | "Kubernetes handles scaling" | Wasting CPU cores |
| Too many workers | "More is better" | OOM kills, memory thrashing |
| Ignoring async | "It's just an API" | 10x-100x lower throughput |
| Same config for all services | "Standardization" | CPU service gets I/O config |

### Right-Sizing Workers vs Pods

```
Given: 8-core nodes, model uses 2GB RAM, node has 16GB

Option A: 1 pod with 8 workers
  Memory: 8 × 2GB = 16GB ✓
  CPU: 8 workers can use 8 cores ✓
  Fault tolerance: Single point of failure ✗

Option B: 2 pods with 4 workers each
  Memory: 2 × (4 × 2GB) = 16GB ✓
  CPU: 8 workers total across 2 pods ✓
  Fault tolerance: One pod can die ✓

Option C: 8 pods with 1 worker each
  Memory: 8 × 2GB = 16GB ✓
  CPU: 8 workers, max distribution ✓
  Fault tolerance: Best ✓
  Overhead: Highest (8 pod networks, probes, etc.) ✗
```

**General rule:** 2-4 workers per pod is a sweet spot for most ML services.

---

## Further Reading

- [FastAPI Async Documentation](https://fastapi.tiangolo.com/async/)
- [Python asyncio Documentation](https://docs.python.org/3/library/asyncio.html)
- [Real Python: Async IO in Python](https://realpython.com/async-io-python/)
- [Uvicorn Settings](https://www.uvicorn.org/settings/)
