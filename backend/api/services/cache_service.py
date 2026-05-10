import asyncio
import hashlib
from typing import Dict, Optional, Any
from datetime import datetime, timedelta
import json

from ..schemas.datasets import FilteredDataset
from ..schemas.health import HealthScorecard

class CacheService:
    def __init__(self):
        # Simple in-memory cache - in production, use Redis
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.cache_ttl: Dict[str, datetime] = {}  # Time-to-live for each cache item

    async def get_filtered_dataset(self, filtered_id: str) -> Optional[FilteredDataset]:
        """Get cached filtered dataset if it exists and hasn't expired"""
        if filtered_id in self.cache:
            if self._is_expired(filtered_id):
                # Remove expired item
                del self.cache[filtered_id]
                del self.cache_ttl[filtered_id]
                return None
            return self.cache[filtered_id]['data']
        return None

    async def cache_filtered_dataset(self, filtered_id: str, filtered_dataset: FilteredDataset, ttl_minutes: int = 60):
        """Cache a filtered dataset with TTL"""
        self.cache[filtered_id] = {
            'data': filtered_dataset,
            'type': 'filtered_dataset'
        }
        self.cache_ttl[filtered_id] = datetime.now() + timedelta(minutes=ttl_minutes)

    async def get_health_score(self, dataset_id: str) -> Optional[HealthScorecard]:
        """Get cached health score if it exists and hasn't expired"""
        cache_key = f"health_{dataset_id}"
        if cache_key in self.cache:
            if self._is_expired(cache_key):
                # Remove expired item
                del self.cache[cache_key]
                del self.cache_ttl[cache_key]
                return None
            return self.cache[cache_key]['data']
        return None

    async def cache_health_score(self, dataset_id: str, health_scorecard: HealthScorecard, ttl_minutes: int = 30):
        """Cache a health score with TTL"""
        cache_key = f"health_{dataset_id}"
        self.cache[cache_key] = {
            'data': health_scorecard,
            'type': 'health_scorecard'
        }
        self.cache_ttl[cache_key] = datetime.now() + timedelta(minutes=ttl_minutes)

    async def get_chart_data(self, chart_key: str) -> Optional[Any]:
        """Get cached chart data if it exists and hasn't expired"""
        if chart_key in self.cache:
            if self._is_expired(chart_key):
                # Remove expired item
                del self.cache[chart_key]
                del self.cache_ttl[chart_key]
                return None
            return self.cache[chart_key]['data']
        return None

    async def cache_chart_data(self, chart_key: str, chart_data: Any, ttl_minutes: int = 120):
        """Cache chart data with TTL"""
        self.cache[chart_key] = {
            'data': chart_data,
            'type': 'chart_data'
        }
        self.cache_ttl[chart_key] = datetime.now() + timedelta(minutes=ttl_minutes)

    def _is_expired(self, key: str) -> bool:
        """Check if a cache item has expired"""
        if key not in self.cache_ttl:
            return True
        return datetime.now() > self.cache_ttl[key]