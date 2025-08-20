# backend/core/middleware.py - Rate limiting and request logging middleware
from fastapi import Request, Response, HTTPException
from fastapi.responses import JSONResponse
import time
import uuid
import logging
from typing import Callable, Dict, Optional
import json
from datetime import datetime, timedelta
from backend.core.redis_cache import cache

logger = logging.getLogger(__name__)

class RateLimiter:
    """Redis-based rate limiter"""
    
    def __init__(
        self,
        requests_per_minute: int = 60,
        requests_per_hour: int = 1000,
        burst_limit: int = 10
    ):
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour
        self.burst_limit = burst_limit
    
    def is_allowed(self, client_id: str) -> tuple[bool, dict]:
        """Check if request is allowed for client"""
        if not cache.is_connected():
            # If Redis is down, allow all requests
            logger.warning("Redis not available, rate limiting disabled")
            return True, {}
        
        current_time = int(time.time())
        minute_key = f"rate_limit:minute:{client_id}:{current_time // 60}"
        hour_key = f"rate_limit:hour:{client_id}:{current_time // 3600}"
        burst_key = f"rate_limit:burst:{client_id}"
        
        try:
            # Check minute limit
            minute_count = cache.get(minute_key, deserialize=False) or "0"
            minute_count = int(minute_count)
            
            if minute_count >= self.requests_per_minute:
                return False, {
                    "error": "RATE_LIMIT_EXCEEDED",
                    "message": f"Rate limit exceeded: {self.requests_per_minute} requests per minute",
                    "retry_after": 60 - (current_time % 60)
                }
            
            # Check hour limit
            hour_count = cache.get(hour_key, deserialize=False) or "0"
            hour_count = int(hour_count)
            
            if hour_count >= self.requests_per_hour:
                return False, {
                    "error": "RATE_LIMIT_EXCEEDED",
                    "message": f"Rate limit exceeded: {self.requests_per_hour} requests per hour",
                    "retry_after": 3600 - (current_time % 3600)
                }
            
            # Check burst limit
            burst_count = cache.get(burst_key, deserialize=False) or "0"
            burst_count = int(burst_count)
            
            if burst_count >= self.burst_limit:
                burst_ttl = cache.ttl(burst_key)
                if burst_ttl > 0:
                    return False, {
                        "error": "BURST_LIMIT_EXCEEDED",
                        "message": f"Burst limit exceeded: {self.burst_limit} requests in 10 seconds",
                        "retry_after": burst_ttl
                    }
            
            # Increment counters
            cache.set(minute_key, str(minute_count + 1), ex=60, serialize=False)
            cache.set(hour_key, str(hour_count + 1), ex=3600, serialize=False)
            cache.set(burst_key, str(burst_count + 1), ex=10, serialize=False)
            
            return True, {
                "requests_remaining_minute": self.requests_per_minute - minute_count - 1,
                "requests_remaining_hour": self.requests_per_hour - hour_count - 1
            }
            
        except Exception as e:
            logger.error(f"Rate limiting error: {e}")
            # Allow request if rate limiting fails
            return True, {}

# Global rate limiter instance
rate_limiter = RateLimiter()

async def rate_limiting_middleware(request: Request, call_next: Callable) -> Response:
    """Rate limiting middleware"""
    
    # Skip rate limiting for health checks
    if request.url.path in ["/health", "/", "/docs", "/redoc", "/openapi.json"]:
        return await call_next(request)
    
    # Get client identifier (IP address for now)
    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")
    client_id = f"{client_ip}:{hash(user_agent) % 10000}"
    
    # Check rate limit
    allowed, rate_info = rate_limiter.is_allowed(client_id)
    
    if not allowed:
        logger.warning(f"Rate limit exceeded for client {client_id} on {request.url.path}")
        return JSONResponse(
            status_code=429,
            content={
                "success": False,
                "error": rate_info.get("error", "RATE_LIMIT_EXCEEDED"),
                "message": rate_info.get("message", "Rate limit exceeded"),
                "retry_after": rate_info.get("retry_after", 60),
                "timestamp": datetime.now().isoformat()
            },
            headers={"Retry-After": str(rate_info.get("retry_after", 60))}
        )
    
    # Add rate limit headers to response
    response = await call_next(request)
    
    if "requests_remaining_minute" in rate_info:
        response.headers["X-RateLimit-Remaining-Minute"] = str(rate_info["requests_remaining_minute"])
    if "requests_remaining_hour" in rate_info:
        response.headers["X-RateLimit-Remaining-Hour"] = str(rate_info["requests_remaining_hour"])
    
    return response

async def request_logging_middleware(request: Request, call_next: Callable) -> Response:
    """Request logging middleware"""
    
    # Generate request ID
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    
    # Log request start
    start_time = time.time()
    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")
    
    # Prepare request log data
    request_data = {
        "request_id": request_id,
        "method": request.method,
        "url": str(request.url),
        "path": request.url.path,
        "client_ip": client_ip,
        "user_agent": user_agent,
        "timestamp": datetime.now().isoformat(),
        "headers": dict(request.headers)
    }
    
    # Log request body for non-GET requests (but not file uploads)
    if request.method in ["POST", "PUT", "PATCH", "DELETE"]:
        content_type = request.headers.get("content-type", "")
        if "application/json" in content_type:
            try:
                body = await request.body()
                if body:
                    request_data["body"] = json.loads(body)
            except:
                pass
    
    logger.info(f"Request started: {request.method} {request.url.path} - ID: {request_id}")
    
    # Process request
    try:
        response = await call_next(request)
        
        # Calculate processing time
        process_time = time.time() - start_time
        
        # Log response
        response_data = {
            "request_id": request_id,
            "status_code": response.status_code,
            "process_time": round(process_time * 1000, 2),  # milliseconds
            "timestamp": datetime.now().isoformat()
        }
        
        # Log based on status code
        if response.status_code < 400:
            logger.info(
                f"Request completed: {request.method} {request.url.path} - "
                f"Status: {response.status_code} - Time: {response_data['process_time']}ms - ID: {request_id}"
            )
        elif response.status_code < 500:
            logger.warning(
                f"Request failed (client error): {request.method} {request.url.path} - "
                f"Status: {response.status_code} - Time: {response_data['process_time']}ms - ID: {request_id}"
            )
        else:
            logger.error(
                f"Request failed (server error): {request.method} {request.url.path} - "
                f"Status: {response.status_code} - Time: {response_data['process_time']}ms - ID: {request_id}"
            )
        
        # Add request ID and processing time to response headers
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time"] = str(response_data['process_time'])
        
        # Store request/response data in cache for debugging (short TTL)
        if cache.is_connected():
            log_data = {**request_data, **response_data}
            cache.set(f"request_log:{request_id}", log_data, ex=300)  # 5 minutes
        
        return response
        
    except Exception as e:
        # Log exception
        process_time = time.time() - start_time
        logger.error(
            f"Request failed (exception): {request.method} {request.url.path} - "
            f"Error: {str(e)} - Time: {round(process_time * 1000, 2)}ms - ID: {request_id}"
        )
        raise

class RequestLoggingConfig:
    """Configuration for request logging"""
    
    def __init__(
        self,
        log_requests: bool = True,
        log_responses: bool = True,
        log_request_body: bool = True,
        log_response_body: bool = False,
        sensitive_fields: Optional[list] = None
    ):
        self.log_requests = log_requests
        self.log_responses = log_responses
        self.log_request_body = log_request_body
        self.log_response_body = log_response_body
        self.sensitive_fields = sensitive_fields or ["password", "token", "key", "secret"]
    
    def sanitize_data(self, data: dict) -> dict:
        """Remove sensitive fields from logged data"""
        if not isinstance(data, dict):
            return data
        
        sanitized = {}
        for key, value in data.items():
            if any(sensitive in key.lower() for sensitive in self.sensitive_fields):
                sanitized[key] = "[REDACTED]"
            elif isinstance(value, dict):
                sanitized[key] = self.sanitize_data(value)
            else:
                sanitized[key] = value
        
        return sanitized

# Global logging config
logging_config = RequestLoggingConfig()

async def security_headers_middleware(request: Request, call_next: Callable) -> Response:
    """Add security headers to responses"""
    response = await call_next(request)
    
    # Add security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    
    # Add CORS headers if not already present
    if "Access-Control-Allow-Origin" not in response.headers:
        response.headers["Access-Control-Allow-Origin"] = "*"
    
    return response