# app/redis_client.py
# A single shared Redis connection, used for publishing diagnostic
# requests to whichever host's channel needs to pick them up.

import redis
from app.config import settings

redis_client = redis.from_url(settings.redis_url, decode_responses=True)