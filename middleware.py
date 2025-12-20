"""Security and rate limiting middleware for FastAPI."""

import time
import threading
from collections import defaultdict
from typing import Callable
from fastapi import Request, HTTPException, status
from fastapi.responses import Response
from starlette.middleware.base import BaseHTTPMiddleware
import logging

logger = logging.getLogger(__name__)

# Thread lock for rate limiting (thread-safe)
_rate_limit_lock = threading.Lock()


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware using sliding window algorithm."""
    
    def __init__(self, app, requests_per_minute: int = 60, window_size: int = 60):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.window_size = window_size
        self.requests = defaultdict(list)
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Check rate limit before processing request (thread-safe)."""
        # Get client identifier (IP address)
        client_ip = request.client.host if request.client else "unknown"
        current_time = time.time()
        
        # Thread-safe rate limit check
        with _rate_limit_lock:
            # Clean old requests outside the window
            if client_ip in self.requests:
                self.requests[client_ip] = [
                    req_time for req_time in self.requests[client_ip]
                    if current_time - req_time < self.window_size
                ]
            
            # Check rate limit
            request_count = len(self.requests[client_ip])
            if request_count >= self.requests_per_minute:
                logger.warning(
                    f"Rate limit exceeded for IP: {client_ip} "
                    f"({request_count}/{self.requests_per_minute} requests)"
                )
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Rate limit exceeded. Maximum {self.requests_per_minute} requests per {self.window_size} seconds."
                )
            
            # Record this request
            self.requests[client_ip].append(current_time)
            remaining = self.requests_per_minute - len(self.requests[client_ip])
        
        # Process request
        try:
            response = await call_next(request)
        except Exception as e:
            logger.error(f"Error processing request from {client_ip}: {str(e)}", exc_info=True)
            raise
        
        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(self.requests_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        
        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Add security headers to response."""
        response = await call_next(request)
        
        # Skip strict CSP for Swagger/OpenAPI docs endpoints
        path = request.url.path
        is_docs_path = path in ["/docs", "/redoc", "/openapi.json"] or path.startswith("/docs/") or path.startswith("/redoc/")
        
        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        if not is_docs_path:
            # Strict headers for API endpoints
            response.headers["X-Frame-Options"] = "DENY"
            response.headers["X-XSS-Protection"] = "1; mode=block"
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
            response.headers["Content-Security-Policy"] = "default-src 'self'"
        else:
            # Relaxed CSP for Swagger UI to allow CDN resources
            response.headers["Content-Security-Policy"] = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net https://unpkg.com; "
                "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://fonts.googleapis.com; "
                "img-src 'self' data: https:; "
                "font-src 'self' data: https://fonts.gstatic.com; "
                "connect-src 'self' https:;"
            )
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        return response

