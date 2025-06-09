import json
import logging
import time
from abc import ABC, abstractmethod
from datetime import datetime, timedelta

import redis

logging.basicConfig(level=logging.INFO)


class RedisClient:
    def __init__(self, host, port, db):
        logging.info(f"Connecting to Redis server at {host}:{port}")
        self.host = host
        self.port = port
        self.db = db
        try:
            self.redis_client = redis.Redis(
                host=self.host, port=self.port, db=self.db, decode_responses=True
            )
            self.redis_client.ping()
        except redis.exceptions.ConnectionError:
            logging.error(
                f"Failed to connect to Redis server at {self.host}:{self.port}"
            )
            return False

    def set_cache(self, key, data, ttl=None):
        self.redis_client.setex(key, ttl, json.dumps(data))

    def get_cache(self, key):
        cached_data = self.redis_client.get(key)
        if cached_data:
            latency = json.loads(cached_data)
            logging.info(f"Cached Latency:{latency}")
            return cached_data
        else:
            logging.info("No cached data found.")
            return False
