"""TTL 記憶體快取工具。

用於 kbars、snapshot 等需要限流保護的端點。
"""
from cachetools import TTLCache

# kbars 快取：最多 200 個 key，每筆有效 60 秒
kbars_cache: TTLCache = TTLCache(maxsize=200, ttl=60)
