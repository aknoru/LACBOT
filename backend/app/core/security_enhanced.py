"""
Enhanced security utilities for LACBOT with advanced protection measures
"""

import os
import time
import hashlib
import ipaddress
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from functools import wraps
import logging
import re
from dataclasses import dataclass
from collections import defaultdict, deque

from fastapi import HTTPException, Request, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from passlib.context import CryptContext
from app.core.config import settings
from app.core.encryption import encryption_manager

logger = logging.getLogger(__name__)

# Enhanced password hashing
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12,  # Increased rounds for better security
    bcrypt__min_rounds=10
)

# Security token management
security = HTTPBearer()

@dataclass
class SecurityEvent:
    """Security event for monitoring"""
    event_type: str
    user_id: Optional[str]
    ip_address: str
    user_agent: str
    timestamp: datetime
    details: Dict[str, Any]
    severity: str = "INFO"

class RateLimiter:
    """Advanced rate limiting with IP and user-based limits"""
    
    def __init__(self):
        self.ip_requests = defaultdict(deque)
        self.user_requests = defaultdict(deque)
        self.blocked_ips = set()
        self.blocked_users = set()
        
    def is_rate_limited(self, identifier: str, limit: int, window: int, 
                       identifier_type: str = "ip") -> Tuple[bool, Dict[str, Any]]:
        """Check if request is rate limited"""
        now = time.time()
        cutoff = now - window
        
        if identifier_type == "ip":
            requests = self.ip_requests[identifier]
        else:
            requests = self.user_requests[identifier]
        
        # Remove old requests
        while requests and requests[0] < cutoff:
            requests.popleft()
        
        # Check if limit exceeded
        if len(requests) >= limit:
            # Add penalty time
            penalty_time = min(300, window * 2)  # Max 5 minutes penalty
            requests.extend([now] * penalty_time)
            
            return True, {
                "limit": limit,
                "window": window,
                "penalty_time": penalty_time,
                "retry_after": penalty_time
            }
        
        # Add current request
        requests.append(now)
        
        return False, {
            "limit": limit,
            "remaining": limit - len(requests),
            "reset_time": now + window
        }
    
    def block_identifier(self, identifier: str, duration: int = 3600, 
                        identifier_type: str = "ip"):
        """Block identifier for specified duration"""
        if identifier_type == "ip":
            self.blocked_ips.add(identifier)
        else:
            self.blocked_users.add(identifier)
        
        # Schedule unblock
        def unblock():
            time.sleep(duration)
            if identifier_type == "ip":
                self.blocked_ips.discard(identifier)
            else:
                self.blocked_users.discard(identifier)
        
        import threading
        threading.Thread(target=unblock, daemon=True).start()
    
    def is_blocked(self, identifier: str, identifier_type: str = "ip") -> bool:
        """Check if identifier is blocked"""
        if identifier_type == "ip":
            return identifier in self.blocked_ips
        else:
            return identifier in self.blocked_users

class InputSanitizer:
    """Advanced input sanitization and validation"""
    
    def __init__(self):
        # Patterns for malicious content
        self.sql_patterns = [
            r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER)\b)",
            r"(\b(UNION|OR|AND)\s+\d+)",
            r"(--|\#|\/\*|\*\/)",
            r"(\b(SCRIPT|JAVASCRIPT|VBSCRIPT)\b)",
        ]
        
        self.xss_patterns = [
            r"<script[^>]*>.*?</script>",
            r"javascript:",
            r"vbscript:",
            r"onload\s*=",
            r"onerror\s*=",
            r"onclick\s*=",
        ]
        
        self.path_traversal_patterns = [
            r"\.\.\/",
            r"\.\.\\\\",
            r"\.\.%2f",
            r"\.\.%5c",
        ]
    
    def sanitize_input(self, input_text: str, input_type: str = "text") -> str:
        """Sanitize input based on type"""
        if not input_text:
            return ""
        
        # Remove null bytes
        input_text = input_text.replace('\x00', '')
        
        # Trim whitespace
        input_text = input_text.strip()
        
        # Check for malicious patterns
        if self._contains_malicious_patterns(input_text):
            logger.warning(f"Malicious input detected: {input_text[:100]}...")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid input detected"
            )
        
        # Type-specific sanitization
        if input_type == "email":
            return self._sanitize_email(input_text)
        elif input_type == "url":
            return self._sanitize_url(input_text)
        elif input_type == "html":
            return self._sanitize_html(input_text)
        else:
            return self._sanitize_text(input_text)
    
    def _contains_malicious_patterns(self, text: str) -> bool:
        """Check for malicious patterns"""
        text_lower = text.lower()
        
        # Check SQL injection patterns
        for pattern in self.sql_patterns:
            if re.search(pattern, text_lower, re.IGNORECASE):
                return True
        
        # Check XSS patterns
        for pattern in self.xss_patterns:
            if re.search(pattern, text_lower, re.IGNORECASE):
                return True
        
        # Check path traversal patterns
        for pattern in self.path_traversal_patterns:
            if re.search(pattern, text_lower, re.IGNORECASE):
                return True
        
        return False
    
    def _sanitize_email(self, email: str) -> str:
        """Sanitize email input"""
        # Basic email validation
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid email format"
            )
        return email.lower()
    
    def _sanitize_url(self, url: str) -> str:
        """Sanitize URL input"""
        # Basic URL validation
        if not url.startswith(('http://', 'https://')):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid URL format"
            )
        return url
    
    def _sanitize_html(self, html: str) -> str:
        """Sanitize HTML input"""
        # Remove script tags and dangerous attributes
        import html
        return html.escape(html)
    
    def _sanitize_text(self, text: str) -> str:
        """Sanitize general text input"""
        # Remove control characters
        text = ''.join(char for char in text if ord(char) >= 32 or char in '\n\t\r')
        
        # Limit length
        if len(text) > 10000:  # 10KB limit
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Input too long"
            )
        
        return text

class SecurityMonitor:
    """Advanced security monitoring and threat detection"""
    
    def __init__(self):
        self.security_events = deque(maxlen=10000)  # Keep last 10k events
        self.failed_logins = defaultdict(list)
        self.suspicious_ips = set()
        self.anomaly_threshold = 5
    
    def log_security_event(self, event: SecurityEvent):
        """Log security event"""
        self.security_events.append(event)
        
        # Check for anomalies
        if event.severity in ["WARNING", "CRITICAL"]:
            self._analyze_threat(event)
    
    def _analyze_threat(self, event: SecurityEvent):
        """Analyze security threat"""
        # Check for brute force attacks
        if event.event_type == "failed_login":
            self.failed_logins[event.ip_address].append(event.timestamp)
            
            # Check if too many failed logins
            recent_failures = [
                failure for failure in self.failed_logins[event.ip_address]
                if failure > datetime.now() - timedelta(minutes=15)
            ]
            
            if len(recent_failures) >= self.anomaly_threshold:
                self.suspicious_ips.add(event.ip_address)
                logger.critical(f"Brute force attack detected from {event.ip_address}")
        
        # Check for unusual patterns
        self._check_anomalies(event)
    
    def _check_anomalies(self, event: SecurityEvent):
        """Check for security anomalies"""
        # Get recent events from same IP
        recent_events = [
            e for e in self.security_events
            if e.ip_address == event.ip_address and
            e.timestamp > datetime.now() - timedelta(hours=1)
        ]
        
        # Check for too many requests
        if len(recent_events) > 100:  # More than 100 requests per hour
            logger.warning(f"High request volume from {event.ip_address}")
        
        # Check for suspicious user agents
        if "bot" in event.user_agent.lower() and "googlebot" not in event.user_agent.lower():
            logger.warning(f"Suspicious user agent from {event.ip_address}: {event.user_agent}")

class EnhancedSecurity:
    """Enhanced security manager with advanced features"""
    
    def __init__(self):
        self.rate_limiter = RateLimiter()
        self.input_sanitizer = InputSanitizer()
        self.security_monitor = SecurityMonitor()
        self.session_store = {}  # In production, use Redis
    
    def create_access_token(self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """Create enhanced JWT access token"""
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        
        # Add security claims
        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "iss": "lacbot-api",
            "aud": "lacbot-client",
            "jti": encryption_manager.generate_session_token(),  # JWT ID
            "version": "1.0"
        })
        
        # Encrypt sensitive claims
        if "sub" in to_encode:
            to_encode["sub"] = encryption_manager.encrypt_sensitive_data(to_encode["sub"])
        
        encoded_jwt = jwt.encode(
            to_encode, 
            settings.SECRET_KEY, 
            algorithm=settings.ALGORITHM
        )
        
        return encoded_jwt
    
    def verify_token(self, token: str) -> Dict[str, Any]:
        """Verify JWT token with enhanced security"""
        try:
            # Decode token
            payload = jwt.decode(
                token, 
                settings.SECRET_KEY, 
                algorithms=[settings.ALGORITHM],
                audience="lacbot-client",
                issuer="lacbot-api"
            )
            
            # Decrypt sensitive claims
            if "sub" in payload:
                payload["sub"] = encryption_manager.decrypt_sensitive_data(payload["sub"])
            
            # Check token version
            if payload.get("version") != "1.0":
                raise jwt.InvalidTokenError("Token version mismatch")
            
            return payload
            
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired"
            )
        except jwt.InvalidTokenError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid token: {str(e)}"
            )
    
    def validate_ip_address(self, ip: str) -> bool:
        """Validate IP address and check against blocklist"""
        try:
            # Check if IP is valid
            ipaddress.ip_address(ip)
            
            # Check if IP is blocked
            if self.rate_limiter.is_blocked(ip, "ip"):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="IP address is blocked"
                )
            
            return True
            
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid IP address"
            )
    
    def check_rate_limit(self, request: Request, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Check rate limiting for request"""
        client_ip = request.client.host
        
        # Validate IP
        self.validate_ip_address(client_ip)
        
        # Check IP-based rate limit
        is_limited, ip_info = self.rate_limiter.is_rate_limited(
            client_ip, 
            settings.RATE_LIMIT_PER_MINUTE, 
            60,  # 1 minute window
            "ip"
        )
        
        if is_limited:
            # Log security event
            event = SecurityEvent(
                event_type="rate_limit_exceeded",
                user_id=user_id,
                ip_address=client_ip,
                user_agent=request.headers.get("user-agent", ""),
                timestamp=datetime.now(),
                details={"limit_info": ip_info},
                severity="WARNING"
            )
            self.security_monitor.log_security_event(event)
            
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded. Try again in {ip_info['retry_after']} seconds",
                headers={"Retry-After": str(ip_info['retry_after'])}
            )
        
        # Check user-based rate limit if user is authenticated
        if user_id:
            is_limited, user_info = self.rate_limiter.is_rate_limited(
                user_id,
                settings.RATE_LIMIT_BURST,
                60,
                "user"
            )
            
            if is_limited:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="User rate limit exceeded"
                )
        
        return {"ip_info": ip_info, "user_info": user_info if user_id else None}

# Global security manager instance
enhanced_security = EnhancedSecurity()

# Decorators for security
def require_authentication(func):
    """Decorator to require authentication"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        # This will be handled by FastAPI dependency injection
        return await func(*args, **kwargs)
    return wrapper

def rate_limit(requests_per_minute: int = 60):
    """Decorator for rate limiting"""
    def decorator(func):
        @wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            enhanced_security.check_rate_limit(request)
            return await func(request, *args, **kwargs)
        return wrapper
    return decorator

def sanitize_input(input_type: str = "text"):
    """Decorator for input sanitization"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Sanitize string arguments
            for key, value in kwargs.items():
                if isinstance(value, str):
                    kwargs[key] = enhanced_security.input_sanitizer.sanitize_input(
                        value, input_type
                    )
            return await func(*args, **kwargs)
        return wrapper
    return decorator

# Enhanced dependency functions
async def get_current_user_enhanced(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    request: Request = None
) -> Dict[str, Any]:
    """Enhanced get current user with security monitoring"""
    token = credentials.credentials
    
    # Log authentication attempt
    event = SecurityEvent(
        event_type="authentication_attempt",
        user_id=None,
        ip_address=request.client.host if request else "unknown",
        user_agent=request.headers.get("user-agent", "") if request else "",
        timestamp=datetime.now(),
        details={"token_length": len(token)},
        severity="INFO"
    )
    enhanced_security.security_monitor.log_security_event(event)
    
    try:
        payload = enhanced_security.verify_token(token)
        user_id = payload.get("sub")
        
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload"
            )
        
        # Log successful authentication
        event = SecurityEvent(
            event_type="authentication_success",
            user_id=user_id,
            ip_address=request.client.host if request else "unknown",
            user_agent=request.headers.get("user-agent", "") if request else "",
            timestamp=datetime.now(),
            details={"user_id": user_id},
            severity="INFO"
        )
        enhanced_security.security_monitor.log_security_event(event)
        
        return {"user_id": user_id, "payload": payload}
        
    except HTTPException as e:
        # Log failed authentication
        event = SecurityEvent(
            event_type="authentication_failure",
            user_id=None,
            ip_address=request.client.host if request else "unknown",
            user_agent=request.headers.get("user-agent", "") if request else "",
            timestamp=datetime.now(),
            details={"error": str(e.detail)},
            severity="WARNING"
        )
        enhanced_security.security_monitor.log_security_event(event)
        raise

def verify_password_enhanced(plain_password: str, hashed_password: str) -> bool:
    """Enhanced password verification"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash_enhanced(password: str) -> str:
    """Enhanced password hashing with salt"""
    return pwd_context.hash(password)

def validate_password_strength(password: str) -> Dict[str, Any]:
    """Validate password strength"""
    score = 0
    feedback = []
    
    # Length check
    if len(password) >= 8:
        score += 1
    else:
        feedback.append("Password should be at least 8 characters long")
    
    # Uppercase check
    if re.search(r'[A-Z]', password):
        score += 1
    else:
        feedback.append("Password should contain at least one uppercase letter")
    
    # Lowercase check
    if re.search(r'[a-z]', password):
        score += 1
    else:
        feedback.append("Password should contain at least one lowercase letter")
    
    # Number check
    if re.search(r'\d', password):
        score += 1
    else:
        feedback.append("Password should contain at least one number")
    
    # Special character check
    if re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        score += 1
    else:
        feedback.append("Password should contain at least one special character")
    
    # Common password check
    common_passwords = ["password", "123456", "qwerty", "abc123", "password123"]
    if password.lower() in common_passwords:
        score -= 2
        feedback.append("Password is too common")
    
    return {
        "score": score,
        "max_score": 5,
        "strength": "weak" if score < 3 else "medium" if score < 4 else "strong",
        "feedback": feedback,
        "is_valid": score >= 3
    }
