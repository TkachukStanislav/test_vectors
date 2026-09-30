from redis.asyncio import Redis

from app.config import settings

redis_client = Redis.from_url(settings.redis_url, decode_responses=True)

JOB_CACHE_TTL = 60


def job_cache_key(job_id: int) -> str:
    return f"job:{job_id}"