from prometheus_client import Counter, Histogram

JOBS_CREATED = Counter("jobs_created_total", "Jobs created via API")
JOBS_PROCESSED = Counter("jobs_processed_total", "Jobs processed by worker", ["status"])
JOB_PROCESSING_SECONDS = Histogram("job_processing_seconds", "Job processing time")