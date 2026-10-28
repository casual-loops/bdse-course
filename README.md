# QueueForge

**A practical laboratory for backend and distributed systems engineering.**

QueueForge is an evolving job-processing system used to investigate concurrency, data correctness, performance, reliability, and operational behavior. The project begins with small, reproducible experiments and grows toward a multi-component backend architecture.

**Status:** Early development. The repository currently contains a PostgreSQL-backed concurrency experiment, not a complete job-processing service.

## What this repository contains

The first experiment examines a fundamental backend correctness problem: **What happens when two workers try to claim the same pending job?**

It compares two implementations:

- **Unsafe claim:** Both workers read the same pending job before updating it. A synchronization barrier makes the race reproducible. The update does not verify that the job is still pending, so both workers may record a successful claim.
- **Safe claim:** A PostgreSQL transaction uses `FOR UPDATE SKIP LOCKED` in a candidate-selection query, followed by an update in the same SQL statement. Concurrent workers compete for an available job without recording duplicate claims.

The demonstration records claim attempts separately from the final job row so the final database state does not conceal the duplicate-claim defect.

### Repository files

| File | Purpose |
| --- | --- |
| `compose.yaml` | Starts a local PostgreSQL 17 container |
| `schema.sql` | Defines the `jobs` and `claim_attempts` tables |
| `race_demo.py` | Runs the unsafe or safe concurrent-claim experiment |
| `requirements.txt` | Lists current Python dependencies |

## Run the first experiment

### Prerequisites

- Python 3.12 or newer
- Docker with Docker Compose
- A local shell with access to the Docker daemon

The commands below are intended for a development environment. The database credentials in `compose.yaml` are **example lab credentials only**, not suitable for a shared or production deployment.

### 1. Clone and prepare Python

```bash
git clone https://github.com/casual-loops/bdse-course.git
cd bdse-course

python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

### 2. Start PostgreSQL

```bash
docker compose up -d
docker compose ps
```

The database uses PostgreSQL 17 and is published on `127.0.0.1:54325`, so it is only exposed on the Docker host's loopback interface by this configuration.

### 3. Create the schema

```bash
docker compose exec -T postgres psql -U queueforge -d queueforge < schema.sql
```

This creates the `jobs` and `claim_attempts` tables used by the experiment.

### 4. Reproduce the race condition

```bash
python race_demo.py unsafe
```

The script resets both lab tables, inserts one pending job, and coordinates two workers to read that job before either updates it. Examine the **worker results**, **final job state**, and **recorded claims**. The key failure is two recorded claims for the same job, even though the job row can only show its final assigned worker.

### 5. Compare the safe implementation

```bash
python race_demo.py safe
```

This mode also resets the lab data, then uses row locking and `SKIP LOCKED`. With a single pending job, at most one worker should return a job ID and record a claim. The other worker should find no available job.

> **Destructive lab operation:** Every run of `race_demo.py` truncates the `jobs` and `claim_attempts` tables and resets their identity sequences. Use only the dedicated lab database.

To stop the container:

```bash
docker compose down
```

## Engineering direction

QueueForge is intended to evolve incrementally. Planned areas of investigation include:

| Area | Questions to investigate |
| --- | --- |
| Transactional correctness | How can conflicting requests maintain business invariants? |
| Database performance | Which query plans, indexes, and connection patterns improve measured behavior? |
| Data evolution | How can schemas change without breaking deployed applications? |
| Caching | What makes cached data stale, and how do concurrent cache misses affect dependencies? |
| Resilience | When are retries safe, and how should failure, rate limits, and backpressure be handled? |
| Asynchronous processing | How do queues, acknowledgments, workers, and idempotency interact? |
| Observability | Which metrics, logs, and traces demonstrate service behavior under load and failure? |

The longer-term target is a job-processing platform built around Python, FastAPI, PostgreSQL, Redis, RabbitMQ, and supporting operational tooling. **These planned technologies and capabilities are not represented as currently implemented.**

## How the work is documented

The repository is an engineering record, not just a collection of finished code. As development continues, individual exercises should include:

1. A clearly defined failure mode or engineering question.
2. A reproducible baseline demonstrating the problem.
3. An implementation and explanation of its tradeoffs.
4. Verification through tests, database observations, logs, or performance measurements.
5. Remaining failure scenarios and operational limitations.

The goal is to make the reasoning and evidence behind each design decision inspectable.

## Project and course

QueueForge is the applied software project developed alongside **Backend & Distributed Systems Engineering**, a structured practical engineering course. This public repository focuses on the implementation, experiments, and technical evidence.

The complete instructional course, including guided lessons, assessments, and supporting learning materials, is a separate work in development and may be offered commercially after completion. This repository should not be interpreted as the full course distribution.

**Project case study:** [QueueForge on mylesh.dev](https://mylesh.dev/work/queueforge)

## License and use

No license has been granted for this repository at this time. Public visibility does not automatically grant permission to copy, modify, or redistribute its contents. A separate software license and course-content terms may be introduced in the future.

---

Maintained by [Myles Hobdy](https://mylesh.dev).
