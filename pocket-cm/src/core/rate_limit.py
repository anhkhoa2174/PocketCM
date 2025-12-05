from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request, HTTPException, status
from typing import Dict
import time
import logging

logger = logging.getLogger(__name__)

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)


class CustomRateLimitExceeded(RateLimitExceeded):
    """Custom rate limit exception with more detailed info"""

    def __init__(self, detail: str):
        super().__init__(detail=detail)


def setup_rate_limits(app):
    """
    Setup rate limiting for the FastAPI application
    """
    # Add rate limit error handler
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    app.state.limiter = limiter

    logger.info("Rate limiting middleware initialized")


def get_rate_limit_headers() -> Dict[str, str]:
    """
    Get rate limit headers for responses
    """
    return {
        "X-RateLimit-Limit": "5",
        "X-RateLimit-Window": "60",
        "X-RateLimit-Remaining": "5",
        "X-RateLimit-Reset": str(int(time.time()) + 60)
    }


def custom_rate_limit_handler(request: Request, exc: RateLimitExceeded):
    """
    Custom handler for rate limit exceeded
    """
    logger.warning(f"Rate limit exceeded for IP: {get_remote_address(request)}")

    raise HTTPException(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        detail={
            "error": "Rate limit exceeded",
            "message": "Too many requests. Please try again later.",
            "retry_after": 60,  # seconds
            "limit": "5 requests per minute"
        },
        headers={
            "Retry-After": "60",
            "X-RateLimit-Limit": "5",
            "X-RateLimit-Window": "60",
            "X-RateLimit-Remaining": "0",
            "X-RateLimit-Reset": str(int(time.time()) + 60)
        }
    )