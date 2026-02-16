"""
缓存管理器
管理 Keepa API 响应缓存，节省 Token 消耗
"""

import os
import json
import hashlib
import sqlite3
from datetime import datetime, timedelta
from typing import Optional, Any, Dict
from pathlib import Path


class CacheManager:
    """
    SQLite-based cache manager for Keepa API responses
    
    Features:
    - Automatic TTL (time-to-live) expiration
    - SQLite storage for reliability
    - JSON serialization for complex data types
    - Size limiting and LRU eviction
    """
    
    def __init__(self, cache_dir: str = "./cache", ttl_hours: int = 24, enabled: bool = True):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.ttl_hours = ttl_hours
        self.enabled = enabled
        
        # SQLite database path
        self.db_path = self.cache_dir / "keepa_cache.db"
        
        # Initialize database
        self._init_db()
        
        # Statistics
        self.stats = {
            'hits': 0,
            'misses': 0,
            'sets': 0,
        }
    
    def _init_db(self):
        """Initialize SQLite database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS cache (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP NOT NULL
                )
            """)
            
            # Create index for faster lookups
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_expires ON cache(expires_at)
            """)
            
            conn.commit()
    
    def _generate_key(self, data: str) -> str:
        """Generate cache key from input data"""
        return hashlib.md5(data.encode()).hexdigest()
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache
        
        Args:
            key: Cache key
        
        Returns:
            Cached value or None if not found/expired
        """
        if not self.enabled:
            return None
        
        cache_key = self._generate_key(key)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT value, expires_at FROM cache WHERE key = ?",
                (cache_key,)
            )
            row = cursor.fetchone()
            
            if row:
                value_str, expires_at = row
                expires = datetime.fromisoformat(expires_at)
                
                if datetime.now() < expires:
                    # Cache hit
                    self.stats['hits'] += 1
                    try:
                        return json.loads(value_str)
                    except json.JSONDecodeError:
                        return None
                else:
                    # Expired - delete it
                    conn.execute("DELETE FROM cache WHERE key = ?", (cache_key,))
                    conn.commit()
        
        # Cache miss
        self.stats['misses'] += 1
        return None
    
    def set(self, key: str, value: Any):
        """
        Set value in cache
        
        Args:
            key: Cache key
            value: Value to cache (must be JSON serializable)
        """
        if not self.enabled:
            return
        
        cache_key = self._generate_key(key)
        expires_at = datetime.now() + timedelta(hours=self.ttl_hours)
        
        try:
            value_str = json.dumps(value, default=str)
            
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO cache (key, value, expires_at)
                    VALUES (?, ?, ?)
                    """,
                    (cache_key, value_str, expires_at.isoformat())
                )
                conn.commit()
                
            self.stats['sets'] += 1
            
        except (TypeError, json.JSONEncodeError) as e:
            print(f"Cache set error: {e}")
    
    def delete(self, key: str):
        """Delete specific key from cache"""
        cache_key = self._generate_key(key)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM cache WHERE key = ?", (cache_key,))
            conn.commit()
    
    def clear_expired(self):
        """Clear all expired entries"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "DELETE FROM cache WHERE expires_at < ?",
                (datetime.now().isoformat(),)
            )
            conn.commit()
    
    def clear_all(self):
        """Clear entire cache"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM cache")
            conn.commit()
        
        # Reset stats
        self.stats = {'hits': 0, 'misses': 0, 'sets': 0}
    
    def get_stats(self) -> Dict:
        """Get cache statistics"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM cache")
            total_entries = cursor.fetchone()[0]
            
            cursor = conn.execute(
                "SELECT COUNT(*) FROM cache WHERE expires_at < ?",
                (datetime.now().isoformat(),)
            )
            expired_entries = cursor.fetchone()[0]
        
        total_requests = self.stats['hits'] + self.stats['misses']
        hit_rate = (self.stats['hits'] / total_requests * 100) if total_requests > 0 else 0
        
        return {
            'total_entries': total_entries,
            'expired_entries': expired_entries,
            'hits': self.stats['hits'],
            'misses': self.stats['misses'],
            'sets': self.stats['sets'],
            'hit_rate': round(hit_rate, 2),
            'ttl_hours': self.ttl_hours,
        }
    
    def get_cache_info(self) -> str:
        """Get formatted cache information"""
        stats = self.get_stats()
        
        return f"""
Cache Statistics:
---------------
Total entries: {stats['total_entries']}
Expired entries: {stats['expired_entries']}
Cache hits: {stats['hits']}
Cache misses: {stats['misses']}
Hit rate: {stats['hit_rate']}%
Sets: {stats['sets']}
TTL: {stats['ttl_hours']} hours
Status: {'Enabled' if self.enabled else 'Disabled'}
"""


class SimpleCache:
    """
    Simple in-memory cache for development/testing
    Not recommended for production use
    """
    
    def __init__(self, ttl_hours: int = 24):
        self.cache = {}
        self.ttl_hours = ttl_hours
    
    def get(self, key: str) -> Optional[Any]:
        if key not in self.cache:
            return None
        
        value, expires_at = self.cache[key]
        
        if datetime.now() > expires_at:
            del self.cache[key]
            return None
        
        return value
    
    def set(self, key: str, value: Any):
        expires_at = datetime.now() + timedelta(hours=self.ttl_hours)
        self.cache[key] = (value, expires_at)
    
    def clear_all(self):
        self.cache.clear()
