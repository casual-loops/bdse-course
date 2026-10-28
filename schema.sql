
CREATE TABLE IF NOT EXISTS jobs (
    id BIGINT GENERATED ALWAYS AS IDENTITY
       PRIMARY KEY,
    status TEXT NOT NULL
       CHECK (status IN ('pending', 'processing')),
    worker_id INTEGER,
    CHECK (
        (status = 'pending' AND worker_id IS NULL)
        OR
        (status = 'processing' AND worker_id IS NOT NULL)
    )
);

CREATE TABLE IF NOT EXISTS claim_attempts (
    id BIGINT GENERATED ALWAYS AS IDENTITY
       PRIMARY KEY,
    job_id BIGINT NOT NULL REFERENCES jobs(id),
    worker_id INTEGER NOT NULL,
    claimed_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
