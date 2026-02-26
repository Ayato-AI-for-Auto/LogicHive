import logging
import httpx
import os
from typing import List, Dict, Optional
from core import config

logger = logging.getLogger(__name__)

class GlobalSearchEngine:
    """
    Communicates with LogicHive Hub for Global Semantic Search.
    Supports search (metadata only) and get_code (full retrieval).
    """
    def __init__(self):
        self.hub_url = config.HUB_URL.rstrip('/')

    async def search(self, query: str, limit: int = 5) -> List[Dict]:
        """Performs semantic search on the Hub (Metadata only)."""
        url = f"{self.hub_url}/api/v1/functions/search"
        payload = {"query": query, "match_count": limit}
        
        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                resp = await client.post(url, json=payload)
                if resp.status_code == 200:
                    return resp.json()
                elif resp.status_code == 429:
                    logger.warning("GlobalSearch: Rate limited by Hub.")
                    return []
                else:
                    logger.error(f"GlobalSearch: Search failed ({resp.status_code}): {resp.text}")
                    return []
        except Exception as e:
            logger.error(f"GlobalSearch: Connection error during search: {e}")
            return []

    async def get_details(self, name: str) -> Optional[Dict]:
        """Retrieves full function details (including code) from the Hub."""
        url = f"{self.hub_url}/api/v1/functions/get_code"
        payload = {"name": name}
        
        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                resp = await client.post(url, json=payload)
                if resp.status_code == 200:
                    return resp.json()
                elif resp.status_code == 429:
                    logger.warning("GlobalSearch: Rate limited for code retrieval.")
                    return None
                else:
                    logger.error(f"GlobalSearch: Retrieval failed ({resp.status_code}): {resp.text}")
                    return None
        except Exception as e:
            logger.error(f"GlobalSearch: Connection error during retrieval: {e}")
            return None

# Singleton
global_search = GlobalSearchEngine()
