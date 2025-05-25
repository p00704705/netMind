import nmap
import json
import time
import pickle
from datetime import datetime, timedelta
from abc import ABC, abstractmethod

class CacheBackend(ABC):
    """Abstract base class for cache backends"""
    
    @abstractmethod
    def get(self, key):
        """Get value from cache by key"""
        pass
    
    @abstractmethod
    def set(self, key, value):
        """Set value in cache with key"""
        pass
    
    @abstractmethod
    def delete(self, key):
        """Delete key from cache"""
        pass
    
    @abstractmethod
    def clear(self):
        """Clear all cache data"""
        pass

class RedisCacheBackend(CacheBackend):
    """Redis-based cache implementation"""
    
    def __init__(self, host='localhost', port=6379, db=0, prefix='nmap_cache:'):
        import redis
        self.redis = redis.Redis(host=host, port=port, db=db)
        self.prefix = prefix
    
    def _get_key(self, key):
        return f"{self.prefix}{key}"
    
    def get(self, key=None):
        if key is None:
            # Get all keys with our prefix
            all_keys = self.redis.keys(f"{self.prefix}*")
            result = {}
            for k in all_keys:
                k_str = k.decode('utf-8')
                clean_key = k_str.replace(self.prefix, '')
                result[clean_key] = json.loads(self.redis.get(k).decode('utf-8'))
            return result
        
        full_key = self._get_key(key)
        data = self.redis.get(full_key)
        return json.loads(data.decode('utf-8')) if data else None
    
    def set(self, key, value, expire_seconds=None):
        full_key = self._get_key(key)
        self.redis.set(full_key, json.dumps(value))
        if expire_seconds:
            self.redis.expire(full_key, expire_seconds)
    
    def delete(self, key):
        self.redis.delete(self._get_key(key))
    
    def clear(self):
        all_keys = self.redis.keys(f"{self.prefix}*")
        if all_keys:
            self.redis.delete(*all_keys)

class MemcachedCacheBackend(CacheBackend):
    """Memcached-based cache implementation"""
    
    def __init__(self, servers=['localhost:11211'], prefix='nmap_cache:'):
        import pymemcache.client
        self.client = pymemcache.client.base.Client(servers)
        self.prefix = prefix
    
    def _get_key(self, key):
        return f"{self.prefix}{key}"
    
    def get(self, key=None):
        # Memcached doesn't support getting all keys natively
        if key is None:
            return {}
        
        data = self.client.get(self._get_key(key))
        return json.loads(data.decode('utf-8')) if data else None
    
    def set(self, key, value, expire_seconds=0):
        self.client.set(self._get_key(key), json.dumps(value), expire=expire_seconds)
    
    def delete(self, key):
        self.client.delete(self._get_key(key))
    
    def clear(self):
        # Memcached doesn't support clearing only our keys
        # You'd need to maintain a list of keys in another key
        # For simplicity, we'll just put a placeholder
        pass

class CachedNmapScanner:
    def __init__(self, cache_backend=None, cache_duration_hours=3):
        """
        Initialize the cached nmap scanner.
        
        Args:
            cache_backend (CacheBackend): Backend to use for caching
            cache_duration_hours (int): How long the cache remains valid in hours
        """
        if cache_backend is None:
            cache_backend = FileCacheBackend()
        
        self.cache_backend = cache_backend
        self.cache_duration = timedelta(hours=cache_duration_hours)
        self.scanner = nmap.PortScanner()
    
    def _is_cache_valid(self, cache_entry):
        """Check if the cache is still valid based on timestamp."""
        if not cache_entry or 'timestamp' not in cache_entry:
            return False
        
        cache_time = datetime.fromisoformat(cache_entry['timestamp'])
        return datetime.now() - cache_time < self.cache_duration
    
    def scan(self, targets, arguments='-sV'):
        """
        Perform an nmap scan, using cache if valid.
        
        Args:
            targets (str): Targets to scan (IP addresses, hostnames, CIDR notation)
            arguments (str): Nmap scan arguments
            
        Returns:
            dict: Scan results
        """
        # Generate a cache key based on targets and scan arguments
        cache_key = f"{targets}_{arguments}"
        
        # Check if we have a valid cached result
        cache_entry = self.cache_backend.get(cache_key)
        
        if cache_entry and self._is_cache_valid(cache_entry):
            print(f"Using cached scan results from {cache_entry.get('timestamp')}")
            return cache_entry.get('results')
        
        # If no valid cache, perform a new scan
        print(f"Performing new nmap scan of {targets}")
        self.scanner.scan(hosts=targets, arguments=arguments)
        
        # Save results to cache
        results = self.scanner.get_nmap_last_output()
        cache_entry = {
            'timestamp': datetime.now().isoformat(),
            'results': results
        }
        
        # For Redis/Memcached, we can set TTL directly in seconds
        if isinstance(self.cache_backend, (RedisCacheBackend, MemcachedCacheBackend)):
            # Convert hours to seconds for TTL
            ttl_seconds = int(self.cache_duration.total_seconds())
            self.cache_backend.set(cache_key, cache_entry, ttl_seconds)
        else:
            self.cache_backend.set(cache_key, cache_entry)
        
        return results
    
    def get_scan_results(self, targets, arguments='-sV', parse_results=True):
        """
        Get scan results with optional parsing.
        
        Args:
            targets (str): Targets to scan
            arguments (str): Nmap scan arguments
            parse_results (bool): Whether to return parsed results
            
        Returns:
            dict: Scan results (parsed or raw depending on parse_results)
        """
        results = self.scan(targets, arguments)
        
        if parse_results:
            # Return the parsed scan results
            return {
                'scan': self.scanner.all_hosts(),
                'hosts': {host: self.scanner[host] for host in self.scanner.all_hosts()}
            }
        
        return results
    
    def clear_cache(self):
        """Clear the cache."""
        self.cache_backend.clear()
        print("Cache cleared")

# Example usage
if __name__ == "__main__":
    # Example 1: File-based cache (default)
    file_scanner = CachedNmapScanner()
    
    # Example 2: Redis cache
    # redis_backend = RedisCacheBackend(host='localhost', port=6379)
    # redis_scanner = CachedNmapScanner(cache_backend=redis_backend, cache_duration_hours=3)
    
    # Example 3: Memcached cache
    # memcached_backend = MemcachedCacheBackend(servers=['localhost:11211'])
    # memcached_scanner = CachedNmapScanner(cache_backend=memcached_backend, cache_duration_hours=3)
    
    # Example 4: DynamoDB cache
    # dynamodb_backend = DynamoDBCacheBackend(table_name='nmap_cache')
    # dynamodb_scanner = CachedNmapScanner(cache_backend=dynamodb_backend, cache_duration_hours=3)
    
    # Run a scan
    results = file_scanner.get_scan_results("127.0.0.1", arguments="-F")
    print(f"Found {len(file_scanner.scanner.all_hosts())} hosts")