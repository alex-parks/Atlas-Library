# backend/core/error_handlers.py - Standardized error handling
from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, ValidationError
from typing import Any, Dict, List, Optional
import logging
import traceback
from datetime import datetime

logger = logging.getLogger(__name__)

# Standard error response models
class ErrorDetail(BaseModel):
    """Individual error detail"""
    field: Optional[str] = None
    message: str
    type: str
    code: Optional[str] = None

class StandardErrorResponse(BaseModel):
    """Standard error response format"""
    success: bool = False
    error: str
    message: str
    details: Optional[List[ErrorDetail]] = None
    timestamp: str
    request_id: Optional[str] = None
    status_code: int

class ValidationErrorResponse(BaseModel):
    """Validation error response"""
    success: bool = False
    error: str = "VALIDATION_ERROR"
    message: str = "Request validation failed"
    validation_errors: List[ErrorDetail]
    timestamp: str
    status_code: int = 422

# Custom exceptions
class BusinessLogicError(Exception):
    """Business logic error"""
    def __init__(self, message: str, code: str = "BUSINESS_ERROR", status_code: int = 400):
        self.message = message
        self.code = code
        self.status_code = status_code
        super().__init__(self.message)

class ResourceNotFoundError(Exception):
    """Resource not found error"""
    def __init__(self, resource_type: str, resource_id: str):
        self.message = f"{resource_type} '{resource_id}' not found"
        self.code = "RESOURCE_NOT_FOUND"
        self.status_code = 404
        super().__init__(self.message)

class DuplicateResourceError(Exception):
    """Duplicate resource error"""
    def __init__(self, resource_type: str, field: str, value: str):
        self.message = f"{resource_type} with {field} '{value}' already exists"
        self.code = "DUPLICATE_RESOURCE"
        self.status_code = 409
        super().__init__(self.message)

class DatabaseError(Exception):
    """Database operation error"""
    def __init__(self, message: str, operation: str = None):
        self.message = f"Database error: {message}"
        if operation:
            self.message = f"Database error in {operation}: {message}"
        self.code = "DATABASE_ERROR"
        self.status_code = 500
        super().__init__(self.message)

class ExternalServiceError(Exception):
    """External service error"""
    def __init__(self, service: str, message: str):
        self.message = f"External service '{service}' error: {message}"
        self.code = "EXTERNAL_SERVICE_ERROR"
        self.status_code = 502
        super().__init__(self.message)

# Error handlers
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handle HTTP exceptions"""
    error_response = StandardErrorResponse(
        error="HTTP_ERROR",
        message=exc.detail,
        timestamp=datetime.now().isoformat(),
        status_code=exc.status_code,
        request_id=getattr(request.state, 'request_id', None)
    )
    
    logger.warning(f"HTTP Error {exc.status_code}: {exc.detail} - Path: {request.url.path}")
    
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response.dict()
    )

async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Handle validation errors"""
    validation_errors = []
    
    for error in exc.errors():
        validation_errors.append(ErrorDetail(
            field=".".join(str(loc) for loc in error["loc"]),
            message=error["msg"],
            type=error["type"],
            code="VALIDATION_ERROR"
        ))
    
    error_response = ValidationErrorResponse(
        validation_errors=validation_errors,
        timestamp=datetime.now().isoformat()
    )
    
    logger.warning(f"Validation Error: {len(validation_errors)} errors - Path: {request.url.path}")
    
    return JSONResponse(
        status_code=422,
        content=error_response.dict()
    )

async def business_logic_exception_handler(request: Request, exc: BusinessLogicError) -> JSONResponse:
    """Handle business logic errors"""
    error_response = StandardErrorResponse(
        error=exc.code,
        message=exc.message,
        timestamp=datetime.now().isoformat(),
        status_code=exc.status_code,
        request_id=getattr(request.state, 'request_id', None)
    )
    
    logger.warning(f"Business Logic Error: {exc.message} - Path: {request.url.path}")
    
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response.dict()
    )

async def resource_not_found_exception_handler(request: Request, exc: ResourceNotFoundError) -> JSONResponse:
    """Handle resource not found errors"""
    error_response = StandardErrorResponse(
        error=exc.code,
        message=exc.message,
        timestamp=datetime.now().isoformat(),
        status_code=exc.status_code,
        request_id=getattr(request.state, 'request_id', None)
    )
    
    logger.warning(f"Resource Not Found: {exc.message} - Path: {request.url.path}")
    
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response.dict()
    )

async def duplicate_resource_exception_handler(request: Request, exc: DuplicateResourceError) -> JSONResponse:
    """Handle duplicate resource errors"""
    error_response = StandardErrorResponse(
        error=exc.code,
        message=exc.message,
        timestamp=datetime.now().isoformat(),
        status_code=exc.status_code,
        request_id=getattr(request.state, 'request_id', None)
    )
    
    logger.warning(f"Duplicate Resource: {exc.message} - Path: {request.url.path}")
    
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response.dict()
    )

async def database_exception_handler(request: Request, exc: DatabaseError) -> JSONResponse:
    """Handle database errors"""
    error_response = StandardErrorResponse(
        error=exc.code,
        message="An internal database error occurred",  # Don't expose internal details
        timestamp=datetime.now().isoformat(),
        status_code=exc.status_code,
        request_id=getattr(request.state, 'request_id', None)
    )
    
    logger.error(f"Database Error: {exc.message} - Path: {request.url.path}")
    
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response.dict()
    )

async def external_service_exception_handler(request: Request, exc: ExternalServiceError) -> JSONResponse:
    """Handle external service errors"""
    error_response = StandardErrorResponse(
        error=exc.code,
        message=exc.message,
        timestamp=datetime.now().isoformat(),
        status_code=exc.status_code,
        request_id=getattr(request.state, 'request_id', None)
    )
    
    logger.error(f"External Service Error: {exc.message} - Path: {request.url.path}")
    
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response.dict()
    )

async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected errors"""
    error_response = StandardErrorResponse(
        error="INTERNAL_ERROR",
        message="An internal server error occurred",
        timestamp=datetime.now().isoformat(),
        status_code=500,
        request_id=getattr(request.state, 'request_id', None)
    )
    
    logger.error(
        f"Unhandled Exception: {str(exc)} - Path: {request.url.path}\n"
        f"Traceback: {traceback.format_exc()}"
    )
    
    return JSONResponse(
        status_code=500,
        content=error_response.dict()
    )

# Helper functions for raising standardized errors
def raise_not_found(resource_type: str, resource_id: str) -> None:
    """Raise a standardized not found error"""
    raise ResourceNotFoundError(resource_type, resource_id)

def raise_duplicate(resource_type: str, field: str, value: str) -> None:
    """Raise a standardized duplicate resource error"""
    raise DuplicateResourceError(resource_type, field, value)

def raise_business_error(message: str, code: str = "BUSINESS_ERROR") -> None:
    """Raise a standardized business logic error"""
    raise BusinessLogicError(message, code)

def raise_database_error(message: str, operation: str = None) -> None:
    """Raise a standardized database error"""
    raise DatabaseError(message, operation)

def raise_external_error(service: str, message: str) -> None:
    """Raise a standardized external service error"""
    raise ExternalServiceError(service, message)

# Request validation helpers
def validate_pagination(limit: int, offset: int) -> None:
    """Validate pagination parameters"""
    if limit < 1 or limit > 1000:
        raise_business_error("Limit must be between 1 and 1000")
    
    if offset < 0:
        raise_business_error("Offset must be non-negative")

def validate_sort_fields(sort_by: str, allowed_fields: List[str]) -> None:
    """Validate sort field"""
    if sort_by not in allowed_fields:
        raise_business_error(f"Sort field must be one of: {', '.join(allowed_fields)}")

# Error response utilities
def create_success_response(data: Any, message: str = "Success") -> Dict[str, Any]:
    """Create a standardized success response"""
    return {
        "success": True,
        "message": message,
        "data": data,
        "timestamp": datetime.now().isoformat()
    }

def create_paginated_response(
    items: List[Any], 
    total: int, 
    limit: int, 
    offset: int,
    message: str = "Success"
) -> Dict[str, Any]:
    """Create a standardized paginated response"""
    return {
        "success": True,
        "message": message,
        "data": {
            "items": items,
            "pagination": {
                "total": total,
                "limit": limit,
                "offset": offset,
                "has_more": (offset + limit) < total,
                "page": (offset // limit) + 1,
                "total_pages": ((total - 1) // limit) + 1 if total > 0 else 0
            }
        },
        "timestamp": datetime.now().isoformat()
    }