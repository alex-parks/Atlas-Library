# backend/core/redis_cache.py - Redis caching utility
import redis
import json
import pickle
import logging
from typing import Any, Optional, Union
from datetime import timedelta
import os
from functools import wraps

logger = logging.getLogger(__name__)

class RedisCache:
    """Redis cache manager for Blacksmith Atlas"""
    
    def __init__(self, host: str = None, port: int = None, db: int = 0):
        self.host = host or os.getenv('REDIS_HOST', 'localhost')
        self.port = port or int(os.getenv('REDIS_PORT', 6379))
        self.db = db
        self.client = None
        self.connected = False
        self._connect()
    
    def _connect(self):
        """Connect to Redis"""
        try:
            self.client = redis.Redis(
                host=self.host,
                port=self.port,
                db=self.db,
                decode_responses=False,
                socket_connect_timeout=5,
                socket_timeout=5
            )
            # Test connection
            self.client.ping()
            self.connected = True
            logger.info(f"✅ Connected to Redis at {self.host}:{self.port}")
        except Exception as e:
            logger.warning(f"❌ Failed to connect to Redis: {e}")
            self.connected = False
    
    def is_connected(self) -> bool:
        """Check if Redis is connected"""
        if not self.client or not self.connected:
            return False
        
        try:
            self.client.ping()
            return True
        except:
            self.connected = False
            return False
    
    def set(
        self, 
        key: str, 
        value: Any, 
        ex: Optional[Union[int, timedelta]] = None,
        serialize: bool = True
    ) -> bool:
        """Set a value in cache"""
        if not self.is_connected():
            logger.warning("Redis not connected, skipping cache set")
            return False
        
        try:
            # Serialize value
            if serialize:
                if isinstance(value, (dict, list)):
                    cache_value = json.dumps(value)
                else:
                    cache_value = pickle.dumps(value)
            else:
                cache_value = value
            
            # Set with expiration
            result = self.client.set(key, cache_value, ex=ex)
            return bool(result)
        except Exception as e:
            logger.error(f"Error setting cache key '{key}': {e}")
            return False
    
    def get(self, key: str, deserialize: bool = True) -> Optional[Any]:
        """Get a value from cache"""
        if not self.is_connected():
            return None
        
        try:
            value = self.client.get(key)
            if value is None:
                return None
            
            # Deserialize value
            if deserialize:
                try:
                    # Try JSON first
                    return json.loads(value)
                except (json.JSONDecodeError, TypeError):
                    try:
                        # Fall back to pickle
                        return pickle.loads(value)
                    except:
                        # Return as string if all else fails
                        return value.decode('utf-8') if isinstance(value, bytes) else value
            else:
                return value.decode('utf-8') if isinstance(value, bytes) else value
                
        except Exception as e:
            logger.error(f"Error getting cache key '{key}': {e}")
            return None
    
    def delete(self, *keys: str) -> int:
        """Delete keys from cache"""
        if not self.is_connected():
            return 0
        
        try:
            return self.client.delete(*keys)
        except Exception as e:
            logger.error(f"Error deleting cache keys {keys}: {e}")
            return 0
    
    def exists(self, key: str) -> bool:
        """Check if key exists in cache"""
        if not self.is_connected():
            return False
        
        try:
            return bool(self.client.exists(key))
        except Exception as e:
            logger.error(f"Error checking cache key '{key}': {e}")
            return False
    
    def expire(self, key: str, time: Union[int, timedelta]) -> bool:
        """Set expiration time for a key"""
        if not self.is_connected():
            return False
        
        try:
            return bool(self.client.expire(key, time))
        except Exception as e:
            logger.error(f"Error setting expiration for key '{key}': {e}")
            return False
    
    def ttl(self, key: str) -> int:
        """Get time to live for a key"""
        if not self.is_connected():
            return -2
        
        try:
            return self.client.ttl(key)
        except Exception as e:
            logger.error(f"Error getting TTL for key '{key}': {e}")
            return -2
    
    def clear_pattern(self, pattern: str) -> int:
        """Clear all keys matching a pattern"""
        if not self.is_connected():
            return 0
        
        try:
            keys = self.client.keys(pattern)
            if keys:
                return self.client.delete(*keys)
            return 0
        except Exception as e:
            logger.error(f"Error clearing pattern '{pattern}': {e}")
            return 0
    
    def get_info(self) -> dict:
        """Get Redis server info"""
        if not self.is_connected():
            return {}
        
        try:
            return self.client.info()
        except Exception as e:
            logger.error(f"Error getting Redis info: {e}")
            return {}

# Global cache instance
cache = RedisCache()

# Cache decorator
def cached(key_prefix: str, expire_time: Union[int, timedelta] = 3600):
    """
    Decorator for caching function results
    
    Usage:
        @cached(key_prefix="assets", expire_time=3600)
        def get_assets():
            return expensive_operation()
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = f"{key_prefix}:{func.__name__}"
            if args:
                cache_key += f":{hash(str(args))}"
            if kwargs:
                cache_key += f":{hash(str(sorted(kwargs.items())))}"
            
            # Try to get from cache first
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Cache hit for key: {cache_key}")
                return cached_result
            
            # Execute function and cache result
            result = await func(*args, **kwargs)
            cache.set(cache_key, result, ex=expire_time)
            logger.debug(f"Cached result for key: {cache_key}")
            
            return result
        return wrapper
    return decorator

# Cache utilities for specific use cases
class AssetCache:
    """Specialized cache for assets"""
    
    @staticmethod
    def get_asset(asset_id: str) -> Optional[dict]:
        """Get cached asset"""
        return cache.get(f"asset:{asset_id}")
    
    @staticmethod
    def set_asset(asset_id: str, asset_data: dict, expire_time: int = 1800):
        """Cache asset data"""
        return cache.set(f"asset:{asset_id}", asset_data, ex=expire_time)
    
    @staticmethod
    def invalidate_asset(asset_id: str):
        """Remove asset from cache"""
        cache.delete(f"asset:{asset_id}")
        # Also clear related searches
        cache.clear_pattern(f"assets:search:*")
    
    @staticmethod
    def get_asset_list(search_key: str) -> Optional[list]:
        """Get cached asset search results"""
        return cache.get(f"assets:search:{search_key}")
    
    @staticmethod
    def set_asset_list(search_key: str, assets: list, expire_time: int = 600):
        """Cache asset search results"""
        return cache.set(f"assets:search:{search_key}", assets, ex=expire_time)

class UserCache:
    """Specialized cache for users"""
    
    @staticmethod
    def get_user(user_id: str) -> Optional[dict]:
        """Get cached user"""
        return cache.get(f"user:{user_id}")
    
    @staticmethod
    def set_user(user_id: str, user_data: dict, expire_time: int = 3600):
        """Cache user data"""
        return cache.set(f"user:{user_id}", user_data, ex=expire_time)
    
    @staticmethod
    def invalidate_user(user_id: str):
        """Remove user from cache"""
        cache.delete(f"user:{user_id}")
        cache.clear_pattern(f"users:*")