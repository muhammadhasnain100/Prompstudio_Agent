"""Utility functions for retry logic, caching, and error handling."""

import time
import asyncio
import hashlib
import json
import logging
import threading
from functools import wraps
from typing import Any, Callable, Optional, Dict
from cachetools import TTLCache
from datetime import datetime

logger = logging.getLogger(__name__)

# Thread-safe cache lock
_cache_lock = threading.Lock()

# Cache for responses (TTL cache with max size and expiration)
response_cache: TTLCache = TTLCache(maxsize=1000, ttl=300)  # 5 minutes TTL, max 1000 entries


def retry_on_failure(
    max_retries: int = 3,
    delay: float = 1.0,
    backoff_factor: float = 2.0,
    exceptions: tuple = (Exception,),
    logger_instance: Optional[logging.Logger] = None
):
    """
    Retry decorator with exponential backoff.
    
    Args:
        max_retries: Maximum number of retry attempts
        delay: Initial delay between retries in seconds
        backoff_factor: Multiplier for delay on each retry
        exceptions: Tuple of exceptions to catch and retry on
        logger_instance: Logger instance for logging retry attempts
    """
    log = logger_instance or logger
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            current_delay = delay
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_retries:
                        log.warning(
                            f"Attempt {attempt + 1}/{max_retries + 1} failed for {func.__name__}: {str(e)}. "
                            f"Retrying in {current_delay:.2f} seconds..."
                        )
                        await asyncio.sleep(current_delay)
                        current_delay *= backoff_factor
                    else:
                        log.error(f"All {max_retries + 1} attempts failed for {func.__name__}: {str(e)}")
            
            # If all retries failed, raise the last exception
            if last_exception:
                raise last_exception
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            current_delay = delay
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_retries:
                        log.warning(
                            f"Attempt {attempt + 1}/{max_retries + 1} failed for {func.__name__}: {str(e)}. "
                            f"Retrying in {current_delay:.2f} seconds..."
                        )
                        time.sleep(current_delay)
                        current_delay *= backoff_factor
                    else:
                        log.error(f"All {max_retries + 1} attempts failed for {func.__name__}: {str(e)}")
            
            # If all retries failed, raise the last exception
            if last_exception:
                raise last_exception
        
        # Return appropriate wrapper based on function type
        import inspect
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def generate_cache_key(request_data: Dict[str, Any]) -> str:
    """
    Generate a cache key from request data.
    
    Args:
        request_data: Request data dictionary
        
    Returns:
        SHA256 hash of the request data
    """
    # Create a stable representation of the request
    # Exclude timestamp and IDs that change between requests
    cache_data = {
        "user_prompt": request_data.get("user_prompt"),
        "user_context": {
            "user_id": request_data.get("user_context", {}).get("user_id"),
            "workspace_id": request_data.get("user_context", {}).get("workspace_id"),
            "organization_id": request_data.get("user_context", {}).get("organization_id"),
        },
        "data_sources": request_data.get("data_sources"),
        "selected_schema_names": request_data.get("selected_schema_names", []),
        "execution_context": request_data.get("execution_context"),
        "ai_model": request_data.get("ai_model"),
        "temperature": request_data.get("temperature"),
        "include_visualization": request_data.get("include_visualization"),
    }
    
    # Create deterministic JSON string
    cache_str = json.dumps(cache_data, sort_keys=True)
    
    # Generate hash
    return hashlib.sha256(cache_str.encode()).hexdigest()


def get_cached_response(cache_key: str) -> Optional[Dict[str, Any]]:
    """
    Get cached response if available (thread-safe).
    
    Args:
        cache_key: Cache key for the request
        
    Returns:
        Cached response dictionary or None if not found
    """
    try:
        with _cache_lock:
            cached = response_cache.get(cache_key)
            if cached:
                logger.debug(f"Cache hit for key: {cache_key[:16]}...")
            return cached
    except Exception as e:
        logger.warning(f"Error getting cached response: {str(e)}", exc_info=True)
        return None


def cache_response(cache_key: str, response_data: Dict[str, Any]) -> None:
    """
    Cache response data (thread-safe).
    
    Args:
        cache_key: Cache key for the request
        response_data: Response data to cache
    """
    try:
        with _cache_lock:
            response_cache[cache_key] = response_data
            logger.debug(f"Cached response for key: {cache_key[:16]}...")
    except Exception as e:
        logger.warning(f"Error caching response: {str(e)}", exc_info=True)


def setup_logging(log_level: str = "INFO") -> None:
    """Setup logging configuration."""
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

