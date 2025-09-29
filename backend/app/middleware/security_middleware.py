"""
Security middleware for LACBOT with comprehensive protection measures
"""

import time
import logging
from typing import Callable
from fastapi import Request, Response, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.core.security_enhanced import enhanced_security, SecurityEvent
from app.core.encryption import encryption_manager
from datetime import datetime

logger = logging.getLogger(__name__)

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware to add security headers to all responses"""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.security_headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
            "Content-Security-Policy": (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: https:; "
                "connect-src 'self' https:; "
                "font-src 'self' data:; "
                "object-src 'none'; "
                "media-src 'self'; "
                "frame-src 'none';"
            ),
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
        }
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        
        # Add security headers
        for header, value in self.security_headers.items():
            response.headers[header] = value
        
        return response

class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware for rate limiting and DDoS protection"""
    
    def __init__(self, app: ASGIApp, requests_per_minute: int = 60):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        client_ip = request.client.host
        
        # Skip rate limiting for health checks
        if request.url.path in ["/health", "/docs", "/redoc", "/openapi.json"]:
            return await call_next(request)
        
        try:
            # Check rate limit
            rate_limit_info = enhanced_security.check_rate_limit(request)
            
            # Add rate limit headers
            response = await call_next(request)
            
            if "ip_info" in rate_limit_info:
                ip_info = rate_limit_info["ip_info"]
                response.headers["X-RateLimit-Limit"] = str(ip_info["limit"])
                response.headers["X-RateLimit-Remaining"] = str(ip_info["remaining"])
                response.headers["X-RateLimit-Reset"] = str(int(ip_info["reset_time"]))
            
            return response
            
        except HTTPException as e:
            if e.status_code == status.HTTP_429_TOO_MANY_REQUESTS:
                # Log rate limit violation
                event = SecurityEvent(
                    event_type="rate_limit_violation",
                    user_id=None,
                    ip_address=client_ip,
                    user_agent=request.headers.get("user-agent", ""),
                    timestamp=datetime.now(),
                    details={"path": str(request.url.path)},
                    severity="WARNING"
                )
                enhanced_security.security_monitor.log_security_event(event)
                
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={"detail": e.detail},
                    headers={"Retry-After": str(e.headers.get("Retry-After", 60))}
                )
            raise

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for comprehensive request logging and monitoring"""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        
        # Extract request information
        client_ip = request.client.host
        user_agent = request.headers.get("user-agent", "")
        method = request.method
        path = str(request.url.path)
        query_params = str(request.query_params)
        
        # Log request
        logger.info(f"Request: {method} {path} from {client_ip}")
        
        try:
            response = await call_next(request)
            
            # Calculate processing time
            process_time = time.time() - start_time
            
            # Log response
            logger.info(
                f"Response: {response.status_code} for {method} {path} "
                f"from {client_ip} in {process_time:.3f}s"
            )
            
            # Add processing time header
            response.headers["X-Process-Time"] = str(process_time)
            
            # Log security event for monitoring
            event = SecurityEvent(
                event_type="request_processed",
                user_id=None,
                ip_address=client_ip,
                user_agent=user_agent,
                timestamp=datetime.now(),
                details={
                    "method": method,
                    "path": path,
                    "status_code": response.status_code,
                    "process_time": process_time,
                    "query_params": query_params
                },
                severity="INFO"
            )
            enhanced_security.security_monitor.log_security_event(event)
            
            return response
            
        except Exception as e:
            # Calculate processing time for errors
            process_time = time.time() - start_time
            
            # Log error
            logger.error(
                f"Error: {str(e)} for {method} {path} "
                f"from {client_ip} in {process_time:.3f}s"
            )
            
            # Log security event for errors
            event = SecurityEvent(
                event_type="request_error",
                user_id=None,
                ip_address=client_ip,
                user_agent=user_agent,
                timestamp=datetime.now(),
                details={
                    "method": method,
                    "path": path,
                    "error": str(e),
                    "process_time": process_time
                },
                severity="ERROR"
            )
            enhanced_security.security_monitor.log_security_event(event)
            
            raise

class InputValidationMiddleware(BaseHTTPMiddleware):
    """Middleware for input validation and sanitization"""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Validate request size
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > 10 * 1024 * 1024:  # 10MB limit
            return JSONResponse(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                content={"detail": "Request too large"}
            )
        
        # Validate content type for POST/PUT requests
        if request.method in ["POST", "PUT", "PATCH"]:
            content_type = request.headers.get("content-type", "")
            
            # Allow JSON and form data
            if not any(ct in content_type for ct in ["application/json", "application/x-www-form-urlencoded", "multipart/form-data"]):
                return JSONResponse(
                    status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                    content={"detail": "Unsupported media type"}
                )
        
        return await call_next(request)

class SecurityAuditMiddleware(BaseHTTPMiddleware):
    """Middleware for security audit and compliance"""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.audit_enabled = True
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if not self.audit_enabled:
            return await call_next(request)
        
        # Create audit trail
        audit_data = {
            "timestamp": datetime.now().isoformat(),
            "ip_address": request.client.host,
            "user_agent": request.headers.get("user-agent", ""),
            "method": request.method,
            "path": str(request.url.path),
            "query_params": dict(request.query_params),
            "headers": dict(request.headers),
            "user_id": None  # Will be populated if user is authenticated
        }
        
        try:
            response = await call_next(request)
            
            # Add response info to audit
            audit_data.update({
                "status_code": response.status_code,
                "response_headers": dict(response.headers)
            })
            
            # Create audit hash for integrity
            audit_hash = encryption_manager.create_audit_hash(audit_data)
            audit_data["audit_hash"] = audit_hash
            
            # Log audit trail (in production, store in secure audit log)
            logger.info(f"Audit: {audit_hash} - {request.method} {request.url.path}")
            
            return response
            
        except Exception as e:
            # Add error info to audit
            audit_data.update({
                "error": str(e),
                "status_code": 500
            })
            
            # Create audit hash for error
            audit_hash = encryption_manager.create_audit_hash(audit_data)
            audit_data["audit_hash"] = audit_hash
            
            # Log error audit
            logger.error(f"Audit Error: {audit_hash} - {str(e)}")
            
            raise

class DataEncryptionMiddleware(BaseHTTPMiddleware):
    """Middleware for automatic data encryption/decryption"""
    
    def __init__(self, app: ASGIApp, encrypt_paths: list = None):
        super().__init__(app)
        # Paths that should have their data encrypted/decrypted
        self.encrypt_paths = encrypt_paths or [
            "/api/chat/message",
            "/api/admin/users",
            "/api/admin/conversations"
        ]
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Check if this path needs encryption handling
        if request.url.path not in self.encrypt_paths:
            return await call_next(request)
        
        try:
            # Process request
            response = await call_next(request)
            
            # Encrypt sensitive response data if needed
            if response.status_code == 200 and "application/json" in response.headers.get("content-type", ""):
                # This would be implemented based on specific data encryption needs
                # For now, we'll just pass through
                pass
            
            return response
            
        except Exception as e:
            logger.error(f"Encryption middleware error: {e}")
            raise

class CSRFProtectionMiddleware(BaseHTTPMiddleware):
    """Middleware for CSRF protection"""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.exempt_paths = ["/health", "/docs", "/redoc", "/openapi.json"]
        self.safe_methods = ["GET", "HEAD", "OPTIONS"]
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip CSRF check for safe methods and exempt paths
        if (request.method in self.safe_methods or 
            request.url.path in self.exempt_paths):
            return await call_next(request)
        
        # Check for CSRF token in headers
        csrf_token = request.headers.get("X-CSRF-Token")
        if not csrf_token:
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={"detail": "CSRF token missing"}
            )
        
        # Validate CSRF token (simplified validation)
        # In production, implement proper CSRF token validation
        if len(csrf_token) < 32:
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={"detail": "Invalid CSRF token"}
            )
        
        return await call_next(request)

class SecurityMonitoringMiddleware(BaseHTTPMiddleware):
    """Middleware for real-time security monitoring"""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.suspicious_patterns = [
            "sqlmap", "nikto", "nmap", "masscan",
            "admin", "root", "administrator",
            "union", "select", "drop", "delete",
            "script", "javascript", "vbscript"
        ]
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        client_ip = request.client.host
        user_agent = request.headers.get("user-agent", "").lower()
        path = str(request.url.path).lower()
        query_params = str(request.query_params).lower()
        
        # Check for suspicious patterns
        suspicious_score = 0
        
        # Check user agent
        for pattern in self.suspicious_patterns:
            if pattern in user_agent:
                suspicious_score += 2
        
        # Check path and query parameters
        for pattern in self.suspicious_patterns:
            if pattern in path or pattern in query_params:
                suspicious_score += 3
        
        # Log suspicious activity
        if suspicious_score > 3:
            event = SecurityEvent(
                event_type="suspicious_activity",
                user_id=None,
                ip_address=client_ip,
                user_agent=user_agent,
                timestamp=datetime.now(),
                details={
                    "path": str(request.url.path),
                    "query_params": str(request.query_params),
                    "suspicious_score": suspicious_score
                },
                severity="WARNING"
            )
            enhanced_security.security_monitor.log_security_event(event)
            
            # Optionally block suspicious requests
            if suspicious_score > 10:
                return JSONResponse(
                    status_code=status.HTTP_403_FORBIDDEN,
                    content={"detail": "Suspicious activity detected"}
                )
        
        return await call_next(request)
