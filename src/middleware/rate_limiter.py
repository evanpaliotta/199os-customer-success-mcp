"""
Redis-based Rate Limiting Middleware for MCP Tools
Implements token bucket algorithm with per-client and per-tool limits
"""

import time
import os
import hashlib
from typing import Optional, Tuple
from functools import wraps
import structlog

logger = structlog.get_logger(__name__)

# Rate limit configuration from environment
RATE_LIMIT_ENABLED = os.getenv('RATE_LIMIT_ENABLED', 'true').lower() == 'true'
MAX_REQUESTS_PER_MINUTE = int(os.getenv('MAX_REQUESTS_PER_MINUTE', '1000'))
MAX_REQUESTS_PER_HOUR = int(os.getenv('MAX_REQUESTS_PER_HOUR', '10000'))
RATE_LIMIT_PER_CLIENT_PER_MINUTE = int(os.getenv('RATE_LIMIT_PER_CLIENT_PER_MINUTE', '100'))


class RateLimitExceeded(Exception):
    """Raised when rate limit is exceeded"""

    def __init__(self, limit_type: str, retry_after: int):
        self.limit_type = limit_type
        self.retry_after = retry_after
        super().__init__(f"Rate limit exceeded: {limit_type}. Retry after {retry_after} seconds")


class RedisRateLimiter:
    """
    Redis-based rate limiter using token bucket algorithm

    Features:
    - Per-client rate limiting
    - Per-tool rate limiting
    - Global rate limiting
    - Automatic key expiration
    - Graceful degradation if Redis unavailable
    """

    def __init__(self):
        """Initialize rate limiter with Redis connection"""
        self.enabled = RATE_LIMIT_ENABLED
        self.redis_client = None

        if self.enabled:
            try:
                import redis
                redis_url = os.getenv('REDIS_URL')

                if redis_url:
                    self.redis_client = redis.from_url(
                        redis_url,
                        socket_connect_timeout=2,
                        socket_timeout=2,
                        decode_responses=True
                    )
                    # Test connection
                    self.redis_client.ping()
                    logger.info("rate_limiter_initialized", redis_url=redis_url.split('@')[-1])
                else:
                    logger.warning("rate_limiter_disabled", reason="REDIS_URL not configured")
                    self.enabled = False

            except Exception as e:
                logger.error("rate_limiter_init_failed", error=str(e))
                self.enabled = False

    def _generate_key(self, identifier: str, window: str) -> str:
        """
        Generate Redis key for rate limiting

        Args:
            identifier: Client ID, tool name, or 'global'
            window: Time window ('minute' or 'hour')

        Returns:
            Redis key string
        """
        # Hash identifier for privacy
        hashed = hashlib.sha256(identifier.encode()).hexdigest()[:16]
        timestamp = int(time.time())

        if window == 'minute':
            bucket = timestamp // 60
        elif window == 'hour':
            bucket = timestamp // 3600
        else:
            bucket = timestamp // 60

        return f"ratelimit:{window}:{hashed}:{bucket}"

    def _check_limit(
        self,
        identifier: str,
        limit: int,
        window: str,
        ttl: int
    ) -> Tuple[bool, int]:
        """
        Check if request is within rate limit

        Args:
            identifier: Unique identifier for this limit (client_id, tool_name, etc.)
            limit: Maximum requests allowed
            window: Time window ('minute' or 'hour')
            ttl: Time-to-live for Redis key in seconds

        Returns:
            Tuple of (allowed: bool, retry_after: int)
        """
        if not self.enabled or not self.redis_client:
            return True, 0

        try:
            key = self._generate_key(identifier, window)

            # Increment counter
            current = self.redis_client.incr(key)

            # Set expiration on first request
            if current == 1:
                self.redis_client.expire(key, ttl)

            # Check if limit exceeded
            if current > limit:
                # Calculate retry_after based on TTL
                ttl_remaining = self.redis_client.ttl(key)
                retry_after = max(ttl_remaining, 0)

                logger.warning(
                    "rate_limit_exceeded",
                    identifier=identifier[:32],  # Truncate for logging
                    window=window,
                    current=current,
                    limit=limit,
                    retry_after=retry_after
                )

                return False, retry_after

            return True, 0

        except Exception as e:
            # Fail open if Redis is unavailable (allows request)
            logger.error("rate_limit_check_failed", error=str(e))
            return True, 0

    def check_client_limit(self, client_id: str) -> Tuple[bool, Optional[int]]:
        """
        Check per-client rate limit

        Args:
            client_id: Client identifier

        Returns:
            Tuple of (allowed: bool, retry_after: Optional[int])
        """
        # Per-minute check
        allowed, retry_after = self._check_limit(
            f"client:{client_id}",
            RATE_LIMIT_PER_CLIENT_PER_MINUTE,
            "minute",
            60
        )

        if not allowed:
            return False, retry_after

        # Per-hour check
        allowed, retry_after = self._check_limit(
            f"client:{client_id}",
            RATE_LIMIT_PER_CLIENT_PER_MINUTE * 60,  # 60 minutes worth
            "hour",
            3600
        )

        return allowed, retry_after if not allowed else None

    def check_tool_limit(self, tool_name: str) -> Tuple[bool, Optional[int]]:
        """
        Check per-tool rate limit

        Args:
            tool_name: Name of the MCP tool

        Returns:
            Tuple of (allowed: bool, retry_after: Optional[int])
        """
        # Per-minute check for this specific tool
        allowed, retry_after = self._check_limit(
            f"tool:{tool_name}",
            MAX_REQUESTS_PER_MINUTE,
            "minute",
            60
        )

        return allowed, retry_after if not allowed else None

    def check_global_limit(self) -> Tuple[bool, Optional[int]]:
        """
        Check global rate limit across all clients and tools

        Returns:
            Tuple of (allowed: bool, retry_after: Optional[int])
        """
        # Global per-minute check
        allowed, retry_after = self._check_limit(
            "global",
            MAX_REQUESTS_PER_MINUTE,
            "minute",
            60
        )

        if not allowed:
            return False, retry_after

        # Global per-hour check
        allowed, retry_after = self._check_limit(
            "global",
            MAX_REQUESTS_PER_HOUR,
            "hour",
            3600
        )

        return allowed, retry_after if not allowed else None

    def check_all_limits(
        self,
        client_id: str,
        tool_name: str
    ) -> Tuple[bool, Optional[str], Optional[int]]:
        """
        Check all rate limits (client, tool, and global)

        Args:
            client_id: Client identifier
            tool_name: Tool name

        Returns:
            Tuple of (allowed: bool, limit_type: Optional[str], retry_after: Optional[int])
        """
        if not self.enabled:
            return True, None, None

        # Check global limit first (fastest to fail)
        allowed, retry_after = self.check_global_limit()
        if not allowed:
            return False, "global", retry_after

        # Check per-client limit
        allowed, retry_after = self.check_client_limit(client_id)
        if not allowed:
            return False, "per_client", retry_after

        # Check per-tool limit
        allowed, retry_after = self.check_tool_limit(tool_name)
        if not allowed:
            return False, "per_tool", retry_after

        return True, None, None


# Global rate limiter instance
_rate_limiter = None


def get_rate_limiter() -> RedisRateLimiter:
    """Get or create global rate limiter instance"""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RedisRateLimiter()
    return _rate_limiter


def rate_limit(func):
    """
    Decorator to apply rate limiting to MCP tool functions

    Usage:
        @rate_limit
        @mcp.tool()
        async def my_tool(ctx: Context, client_id: str, ...):
            ...

    The decorated function must have a 'client_id' parameter.
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        # Extract client_id from kwargs
        client_id = kwargs.get('client_id', 'unknown')
        tool_name = func.__name__

        # Get rate limiter
        limiter = get_rate_limiter()

        # Check rate limits
        allowed, limit_type, retry_after = limiter.check_all_limits(client_id, tool_name)

        if not allowed:
            error_msg = (
                f"Rate limit exceeded for {limit_type}. "
                f"Retry after {retry_after} seconds."
            )

            logger.warning(
                "rate_limit_rejected",
                client_id=client_id[:32],
                tool_name=tool_name,
                limit_type=limit_type,
                retry_after=retry_after
            )

            # Return error response in MCP-compatible format
            return {
                "status": "error",
                "error": error_msg,
                "error_code": "RATE_LIMIT_EXCEEDED",
                "limit_type": limit_type,
                "retry_after": retry_after
            }

        # Execute the function
        return await func(*args, **kwargs)

    return wrapper


def check_rate_limit_sync(client_id: str, tool_name: str) -> dict:
    """
    Synchronous rate limit check for non-async contexts

    Args:
        client_id: Client identifier
        tool_name: Tool name

    Returns:
        Dict with 'allowed' bool and optional 'retry_after' int
    """
    limiter = get_rate_limiter()
    allowed, limit_type, retry_after = limiter.check_all_limits(client_id, tool_name)

    return {
        "allowed": allowed,
        "limit_type": limit_type,
        "retry_after": retry_after
    }
