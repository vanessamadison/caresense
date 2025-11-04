"""Rate limiting middleware for API protection."""

from __future__ import annotations

import time
from collections import defaultdict
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.status import HTTP_429_TOO_MANY_REQUESTS

from caresense.utils.logging import get_logger

log = get_logger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Token bucket rate limiting middleware.

    Security features:
    - Per-IP rate limiting
    - Per-endpoint rate limiting
    - Configurable limits
    - Automatic cleanup of old entries
    - Audit logging of violations
    """

    def __init__(
        self,
        app,
        requests_per_minute: int = 60,
        burst_size: int = 10,
    ):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.burst_size = burst_size
        self.rate_per_second = requests_per_minute / 60.0

        # Store: {client_ip: {endpoint: (tokens, last_update)}}
        self._buckets: dict[str, dict[str, tuple[float, float]]] = defaultdict(dict)

        # Last cleanup time
        self._last_cleanup = time.time()

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with rate limiting."""
        # Get client IP
        client_ip = self._get_client_ip(request)

        # Get endpoint
        endpoint = f"{request.method}:{request.url.path}"

        # Check rate limit
        if not self._check_rate_limit(client_ip, endpoint):
            log.warning(
                "rate_limit_exceeded",
                client_ip=client_ip,
                endpoint=endpoint,
            )

            return Response(
                content='{"detail":"Rate limit exceeded. Please try again later."}',
                status_code=HTTP_429_TOO_MANY_REQUESTS,
                media_type="application/json",
                headers={
                    "Retry-After": "60",
                    "X-RateLimit-Limit": str(self.requests_per_minute),
                    "X-RateLimit-Remaining": "0",
                },
            )

        # Process request
        response = await call_next(request)

        # Add rate limit headers
        remaining = self._get_remaining_requests(client_ip, endpoint)
        response.headers["X-RateLimit-Limit"] = str(self.requests_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(max(0, int(remaining)))

        # Periodic cleanup
        if time.time() - self._last_cleanup > 3600:  # Every hour
            self._cleanup_old_entries()

        return response

    def _get_client_ip(self, request: Request) -> str:
        """
        Extract client IP from request.

        Security: Checks X-Forwarded-For header for proxy support
        """
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            # Take first IP in chain
            return forwarded.split(",")[0].strip()

        return request.client.host if request.client else "unknown"

    def _check_rate_limit(self, client_ip: str, endpoint: str) -> bool:
        """
        Check if request is within rate limit using token bucket algorithm.

        Args:
            client_ip: Client IP address
            endpoint: Request endpoint

        Returns:
            True if request allowed, False if rate limited
        """
        current_time = time.time()

        # Get or create bucket
        if endpoint not in self._buckets[client_ip]:
            self._buckets[client_ip][endpoint] = (float(self.burst_size), current_time)

        tokens, last_update = self._buckets[client_ip][endpoint]

        # Calculate tokens to add
        time_passed = current_time - last_update
        tokens_to_add = time_passed * self.rate_per_second

        # Update tokens (capped at burst size)
        tokens = min(self.burst_size, tokens + tokens_to_add)

        # Check if request allowed
        if tokens >= 1.0:
            # Consume one token
            tokens -= 1.0
            self._buckets[client_ip][endpoint] = (tokens, current_time)
            return True
        else:
            # Rate limited
            self._buckets[client_ip][endpoint] = (tokens, current_time)
            return False

    def _get_remaining_requests(self, client_ip: str, endpoint: str) -> float:
        """Get remaining requests in bucket."""
        if endpoint not in self._buckets[client_ip]:
            return float(self.burst_size)

        tokens, _ = self._buckets[client_ip][endpoint]
        return tokens

    def _cleanup_old_entries(self) -> None:
        """Remove old inactive buckets to prevent memory growth."""
        current_time = time.time()
        clients_to_remove = []

        for client_ip, endpoints in self._buckets.items():
            endpoints_to_remove = []

            for endpoint, (tokens, last_update) in endpoints.items():
                # Remove buckets inactive for >1 hour
                if current_time - last_update > 3600:
                    endpoints_to_remove.append(endpoint)

            for endpoint in endpoints_to_remove:
                del endpoints[endpoint]

            if not endpoints:
                clients_to_remove.append(client_ip)

        for client_ip in clients_to_remove:
            del self._buckets[client_ip]

        self._last_cleanup = current_time

        log.info("rate_limit_cleanup", clients_removed=len(clients_to_remove))
