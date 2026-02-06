"""
Authentication and Authorization Middleware
API Key authentication with rate limiting support
"""

from fastapi import HTTPException, Security, Request
from fastapi.security import APIKeyHeader
from typing import Optional
import time
from collections import defaultdict
import logging

from .config import settings

logger = logging.getLogger(__name__)

# API Key header configuration
API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)


class RateLimiter:
    """
    In-memory rate limiter
    In production, use Redis for distributed rate limiting
    """
    
    def __init__(self):
        self.requests: dict = defaultdict(list)
        self.limits = {
            'per_minute': settings.rate_limit_per_minute,
            'per_hour': settings.rate_limit_per_hour
        }
    
    def _cleanup_old_requests(self, api_key: str, window_seconds: int) -> list:
        """Remove requests older than the window"""
        current_time = time.time()
        cutoff = current_time - window_seconds
        
        self.requests[api_key] = [
            ts for ts in self.requests[api_key] 
            if ts > cutoff
        ]
        
        return self.requests[api_key]
    
    def check_rate_limit(self, api_key: str) -> tuple[bool, Optional[str]]:
        """
        Check if request is within rate limits
        
        Returns:
            (is_allowed, error_message)
        """
        current_time = time.time()
        
        # Check per-minute limit
        minute_requests = self._cleanup_old_requests(api_key, 60)
        if len(minute_requests) >= self.limits['per_minute']:
            return False, f"Rate limit exceeded: {self.limits['per_minute']} requests per minute"
        
        # Check per-hour limit
        hour_requests = self._cleanup_old_requests(api_key, 3600)
        if len(hour_requests) >= self.limits['per_hour']:
            return False, f"Rate limit exceeded: {self.limits['per_hour']} requests per hour"
        
        # Record this request
        self.requests[api_key].append(current_time)
        
        return True, None
    
    def get_remaining(self, api_key: str) -> dict:
        """Get remaining rate limits for an API key"""
        self._cleanup_old_requests(api_key, 3600)
        
        minute_requests = len([
            ts for ts in self.requests[api_key]
            if ts > time.time() - 60
        ])
        hour_requests = len(self.requests[api_key])
        
        return {
            'remaining_per_minute': max(0, self.limits['per_minute'] - minute_requests),
            'remaining_per_hour': max(0, self.limits['per_hour'] - hour_requests)
        }


# Global rate limiter instance
rate_limiter = RateLimiter()


async def verify_api_key(
    request: Request,
    api_key: Optional[str] = Security(API_KEY_HEADER)
) -> str:
    """
    Verify API key and check rate limits
    
    Raises:
        HTTPException: If API key is invalid or rate limit exceeded
    """
    # Check if API key is provided
    if not api_key:
        logger.warning(f"Missing API key from {request.client.host}")
        raise HTTPException(
            status_code=401,
            detail="API key required. Include X-API-Key header.",
            headers={"WWW-Authenticate": "ApiKey"}
        )
    
    # Validate API key
    if api_key not in settings.api_keys:
        logger.warning(f"Invalid API key attempt: {api_key[:8]}...")
        raise HTTPException(
            status_code=403,
            detail="Invalid API key"
        )
    
    # Check rate limiting
    is_allowed, error_message = rate_limiter.check_rate_limit(api_key)
    if not is_allowed:
        logger.warning(f"Rate limit exceeded for key: {api_key[:8]}...")
        
        remaining = rate_limiter.get_remaining(api_key)
        raise HTTPException(
            status_code=429,
            detail=error_message,
            headers={
                "X-RateLimit-Remaining-Minute": str(remaining['remaining_per_minute']),
                "X-RateLimit-Remaining-Hour": str(remaining['remaining_per_hour']),
                "Retry-After": "60"
            }
        )
    
    logger.debug(f"Authenticated request with key: {api_key[:8]}...")
    return api_key


def get_rate_limit_headers(api_key: str) -> dict:
    """Get rate limit headers for response"""
    remaining = rate_limiter.get_remaining(api_key)
    return {
        "X-RateLimit-Limit-Minute": str(settings.rate_limit_per_minute),
        "X-RateLimit-Limit-Hour": str(settings.rate_limit_per_hour),
        "X-RateLimit-Remaining-Minute": str(remaining['remaining_per_minute']),
        "X-RateLimit-Remaining-Hour": str(remaining['remaining_per_hour'])
    }
