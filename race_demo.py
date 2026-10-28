
import os
import sys
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import psycopg

DSN = os.getenv(
    "DATABASE_URL",
    "postgresql://queueforge:queueforge_lab"
    "@localhost:54325/queueforge",
)


def reset_database():
    with psycopg.connect(DSN) as conn:
        conn.execute(
            "TRUNCATE claim_attempts, jobs RESTART IDENTITY CASCADE"
        )

        result = conn.execute(
            """
            INSERT INTO jobs (status)
            VALUES ('pending')
            RETURNING id
            """
        ).fetchone()

        if result is None:
            raise RuntimeError(
                "Failed to create the initial test job."
            )

        job_id = result[0]
        return job_id


def unsafe_claim(worker_id, barrier):
    with psycopg.connect(DSN) as conn:
        with conn.transaction():
            row = conn.execute(
                """
                SELECT id
                FROM jobs
                WHERE status = 'pending'
                ORDER BY id
                LIMIT 1
                """
            ).fetchone()

            # Synchronize both workers after reading.
            barrier.wait(timeout=10)

            if row is None:
                return None

            job_id = row[0]

            # Deliberately unsafe unconditional update.
            conn.execute(
                """
                UPDATE jobs
                SET status = 'processing',
                    worker_id = %s
                WHERE id = %s
                """,
                (worker_id, job_id),
            )

            conn.execute(
                """
                INSERT INTO claim_attempts
                    (job_id, worker_id)
                VALUES (%s, %s)
                """,
                (job_id, worker_id),
            )

            return job_id



def run_experiment(claim_function, synchronize=False):
    job_id = reset_database()

    barrier = Barrier(2, timeout=10) if synchronize else None

    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [
            executor.submit(claim_function, worker_id, barrier)
            for worker_id in (101, 102)
        ]
        results = [future.result() for future in futures]

    with psycopg.connect(DSN) as conn:
        job = conn.execute(
            "SELECT id, status, worker_id FROM jobs WHERE id = %s",
            (job_id,),
        ).fetchone()

        claims = conn.execute(
            """
            SELECT worker_id
            FROM claim_attempts
            WHERE job_id = %s
            ORDER BY id
            """,
            (job_id,),
        ).fetchall()

    return results, job, [row[0] for row in claims]



def safe_claim(worker_id, barrier=None):
    with psycopg.connect(DSN) as conn:
        with conn.transaction():
            row = conn.execute(
                """
                WITH candidate AS (
                    SELECT id
                    FROM jobs
                    WHERE status = 'pending'
                    ORDER BY id
                    FOR UPDATE SKIP LOCKED
                    LIMIT 1
                )
                UPDATE jobs AS j
                SET status = 'processing',
                    worker_id = %s
                FROM candidate AS c
                WHERE j.id = c.id
                RETURNING j.id
                """,
                (worker_id,),
            ).fetchone()

            if row is None:
                return None

            job_id = row[0]

            conn.execute(
                """
                INSERT INTO claim_attempts
                    (job_id, worker_id)
                VALUES (%s, %s)
                """,
                (job_id, worker_id),
            )

            return job_id


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "unsafe"

    if mode == "unsafe":
        result = run_experiment(unsafe_claim, synchronize=True)
    elif mode == "safe":
        result = run_experiment(safe_claim)
    else:
        raise SystemExit("Choose 'unsafe' or 'safe'")

    results, job, claims = result
    print(f"Worker results: {results}")
    print(f"Final job state: {job}")
    print(f"Recorded claims: {claims}")
