"""
Security API routes for monitoring, audit, and security management
"""

from fastapi import APIRouter, HTTPException, Depends, status, Request
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import logging

from app.core.security_enhanced import (
    enhanced_security, 
    get_current_user_enhanced,
    validate_password_strength,
    SecurityEvent
)
from app.core.encryption import encryption_manager

router = APIRouter()
logger = logging.getLogger(__name__)

# Request/Response models
class SecurityEventResponse(BaseModel):
    event_type: str
    user_id: Optional[str]
    ip_address: str
    user_agent: str
    timestamp: datetime
    details: Dict[str, Any]
    severity: str

class PasswordStrengthRequest(BaseModel):
    password: str = Field(..., min_length=1, max_length=100)

class PasswordStrengthResponse(BaseModel):
    score: int
    max_score: int
    strength: str
    feedback: List[str]
    is_valid: bool

class SecurityAuditRequest(BaseModel):
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    event_type: Optional[str] = None
    severity: Optional[str] = None
    ip_address: Optional[str] = None
    limit: int = Field(100, ge=1, le=1000)

class SecurityMetricsResponse(BaseModel):
    total_events: int
    events_by_type: Dict[str, int]
    events_by_severity: Dict[str, int]
    top_ips: List[Dict[str, Any]]
    recent_events: List[SecurityEventResponse]
    security_score: float

class BlockIPRequest(BaseModel):
    ip_address: str = Field(..., description="IP address to block")
    duration: int = Field(3600, ge=60, le=86400, description="Block duration in seconds")
    reason: str = Field(..., min_length=1, max_length=200)

class UnblockIPRequest(BaseModel):
    ip_address: str = Field(..., description="IP address to unblock")

@router.get("/events", response_model=List[SecurityEventResponse])
async def get_security_events(
    request: Request,
    audit_request: SecurityAuditRequest = Depends(),
    current_user: Dict[str, Any] = Depends(get_current_user_enhanced)
):
    """
    Get security events with filtering options (Super User only)
    """
    try:
        # Check if user has superuser privileges
        if current_user.get("role") != "superuser":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Super user privileges required"
            )
        
        # Get events from security monitor
        events = list(enhanced_security.security_monitor.security_events)
        
        # Apply filters
        filtered_events = []
        for event in events:
            # Date filter
            if audit_request.start_date and event.timestamp < audit_request.start_date:
                continue
            if audit_request.end_date and event.timestamp > audit_request.end_date:
                continue
            
            # Event type filter
            if audit_request.event_type and event.event_type != audit_request.event_type:
                continue
            
            # Severity filter
            if audit_request.severity and event.severity != audit_request.severity:
                continue
            
            # IP filter
            if audit_request.ip_address and event.ip_address != audit_request.ip_address:
                continue
            
            filtered_events.append(event)
        
        # Sort by timestamp (newest first)
        filtered_events.sort(key=lambda x: x.timestamp, reverse=True)
        
        # Apply limit
        filtered_events = filtered_events[:audit_request.limit]
        
        # Convert to response format
        response_events = []
        for event in filtered_events:
            response_events.append(SecurityEventResponse(
                event_type=event.event_type,
                user_id=event.user_id,
                ip_address=event.ip_address,
                user_agent=event.user_agent,
                timestamp=event.timestamp,
                details=event.details,
                severity=event.severity
            ))
        
        return response_events
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get security events: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve security events"
        )

@router.get("/metrics", response_model=SecurityMetricsResponse)
async def get_security_metrics(
    current_user: Dict[str, Any] = Depends(get_current_user_enhanced)
):
    """
    Get security metrics and dashboard data (Super User only)
    """
    try:
        # Check if user has superuser privileges
        if current_user.get("role") != "superuser":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Super user privileges required"
            )
        
        events = list(enhanced_security.security_monitor.security_events)
        
        # Calculate metrics
        total_events = len(events)
        
        # Events by type
        events_by_type = {}
        for event in events:
            events_by_type[event.event_type] = events_by_type.get(event.event_type, 0) + 1
        
        # Events by severity
        events_by_severity = {}
        for event in events:
            events_by_severity[event.severity] = events_by_severity.get(event.severity, 0) + 1
        
        # Top IPs by event count
        ip_counts = {}
        for event in events:
            ip_counts[event.ip_address] = ip_counts.get(event.ip_address, 0) + 1
        
        top_ips = []
        for ip, count in sorted(ip_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
            top_ips.append({
                "ip_address": ip,
                "event_count": count,
                "is_blocked": enhanced_security.rate_limiter.is_blocked(ip, "ip")
            })
        
        # Recent events (last 10)
        recent_events = sorted(events, key=lambda x: x.timestamp, reverse=True)[:10]
        recent_events_response = []
        for event in recent_events:
            recent_events_response.append(SecurityEventResponse(
                event_type=event.event_type,
                user_id=event.user_id,
                ip_address=event.ip_address,
                user_agent=event.user_agent,
                timestamp=event.timestamp,
                details=event.details,
                severity=event.severity
            ))
        
        # Calculate security score (0-100)
        security_score = 100.0
        
        # Deduct points for security issues
        critical_events = events_by_severity.get("CRITICAL", 0)
        warning_events = events_by_severity.get("WARNING", 0)
        error_events = events_by_severity.get("ERROR", 0)
        
        security_score -= critical_events * 10  # -10 points per critical event
        security_score -= warning_events * 2    # -2 points per warning
        security_score -= error_events * 5      # -5 points per error
        
        # Ensure score doesn't go below 0
        security_score = max(0, security_score)
        
        return SecurityMetricsResponse(
            total_events=total_events,
            events_by_type=events_by_type,
            events_by_severity=events_by_severity,
            top_ips=top_ips,
            recent_events=recent_events_response,
            security_score=security_score
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get security metrics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve security metrics"
        )

@router.post("/password-strength", response_model=PasswordStrengthResponse)
async def check_password_strength(password_request: PasswordStrengthRequest):
    """
    Check password strength without requiring authentication
    """
    try:
        strength_result = validate_password_strength(password_request.password)
        
        return PasswordStrengthResponse(
            score=strength_result["score"],
            max_score=strength_result["max_score"],
            strength=strength_result["strength"],
            feedback=strength_result["feedback"],
            is_valid=strength_result["is_valid"]
        )
        
    except Exception as e:
        logger.error(f"Failed to check password strength: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to check password strength"
        )

@router.post("/block-ip")
async def block_ip_address(
    block_request: BlockIPRequest,
    current_user: Dict[str, Any] = Depends(get_current_user_enhanced)
):
    """
    Block an IP address (Super User only)
    """
    try:
        # Check if user has superuser privileges
        if current_user.get("role") != "superuser":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Super user privileges required"
            )
        
        # Block the IP
        enhanced_security.rate_limiter.block_identifier(
            block_request.ip_address,
            block_request.duration,
            "ip"
        )
        
        # Log the blocking action
        event = SecurityEvent(
            event_type="ip_blocked",
            user_id=current_user.get("user_id"),
            ip_address=block_request.ip_address,
            user_agent="System",
            timestamp=datetime.now(),
            details={
                "blocked_by": current_user.get("user_id"),
                "duration": block_request.duration,
                "reason": block_request.reason
            },
            severity="WARNING"
        )
        enhanced_security.security_monitor.log_security_event(event)
        
        return {
            "message": f"IP address {block_request.ip_address} blocked for {block_request.duration} seconds",
            "reason": block_request.reason
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to block IP address: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to block IP address"
        )

@router.post("/unblock-ip")
async def unblock_ip_address(
    unblock_request: UnblockIPRequest,
    current_user: Dict[str, Any] = Depends(get_current_user_enhanced)
):
    """
    Unblock an IP address (Super User only)
    """
    try:
        # Check if user has superuser privileges
        if current_user.get("role") != "superuser":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Super user privileges required"
            )
        
        # Unblock the IP
        enhanced_security.rate_limiter.blocked_ips.discard(unblock_request.ip_address)
        
        # Log the unblocking action
        event = SecurityEvent(
            event_type="ip_unblocked",
            user_id=current_user.get("user_id"),
            ip_address=unblock_request.ip_address,
            user_agent="System",
            timestamp=datetime.now(),
            details={
                "unblocked_by": current_user.get("user_id")
            },
            severity="INFO"
        )
        enhanced_security.security_monitor.log_security_event(event)
        
        return {
            "message": f"IP address {unblock_request.ip_address} unblocked"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to unblock IP address: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to unblock IP address"
        )

@router.get("/blocked-ips")
async def get_blocked_ips(
    current_user: Dict[str, Any] = Depends(get_current_user_enhanced)
):
    """
    Get list of blocked IP addresses (Super User only)
    """
    try:
        # Check if user has superuser privileges
        if current_user.get("role") != "superuser":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Super user privileges required"
            )
        
        blocked_ips = list(enhanced_security.rate_limiter.blocked_ips)
        
        return {
            "blocked_ips": blocked_ips,
            "count": len(blocked_ips)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get blocked IPs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve blocked IPs"
        )

@router.get("/rate-limit-status")
async def get_rate_limit_status(
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user_enhanced)
):
    """
    Get current rate limit status for the requesting IP
    """
    try:
        client_ip = request.client.host
        
        # Get rate limit information
        ip_requests = enhanced_security.rate_limiter.ip_requests.get(client_ip, [])
        user_requests = enhanced_security.rate_limiter.user_requests.get(current_user.get("user_id"), [])
        
        now = time.time()
        cutoff_1min = now - 60
        cutoff_1hour = now - 3600
        
        # Count requests in different time windows
        ip_requests_1min = len([r for r in ip_requests if r > cutoff_1min])
        ip_requests_1hour = len([r for r in ip_requests if r > cutoff_1hour])
        
        user_requests_1min = len([r for r in user_requests if r > cutoff_1min])
        user_requests_1hour = len([r for r in user_requests if r > cutoff_1hour])
        
        return {
            "ip_address": client_ip,
            "user_id": current_user.get("user_id"),
            "rate_limits": {
                "ip_requests_1min": ip_requests_1min,
                "ip_requests_1hour": ip_requests_1hour,
                "user_requests_1min": user_requests_1min,
                "user_requests_1hour": user_requests_1hour
            },
            "limits": {
                "ip_per_minute": 60,
                "user_per_minute": 100
            },
            "is_blocked": enhanced_security.rate_limiter.is_blocked(client_ip, "ip")
        }
        
    except Exception as e:
        logger.error(f"Failed to get rate limit status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve rate limit status"
        )

@router.get("/security-config")
async def get_security_config(
    current_user: Dict[str, Any] = Depends(get_current_user_enhanced)
):
    """
    Get current security configuration (Super User only)
    """
    try:
        # Check if user has superuser privileges
        if current_user.get("role") != "superuser":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Super user privileges required"
            )
        
        return {
            "rate_limits": {
                "requests_per_minute": 60,
                "burst_limit": 100
            },
            "security_features": {
                "rate_limiting": True,
                "input_validation": True,
                "encryption": True,
                "audit_logging": True,
                "csrf_protection": True,
                "security_headers": True
            },
            "encryption": {
                "algorithm": "AES-256-GCM",
                "key_rotation": False,
                "data_at_rest": True,
                "data_in_transit": True
            },
            "monitoring": {
                "security_events": True,
                "anomaly_detection": True,
                "threat_detection": True,
                "audit_trail": True
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get security config: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve security configuration"
        )

@router.post("/generate-api-key")
async def generate_api_key(
    current_user: Dict[str, Any] = Depends(get_current_user_enhanced)
):
    """
    Generate a new API key for the user (Super User only)
    """
    try:
        # Check if user has superuser privileges
        if current_user.get("role") != "superuser":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Super user privileges required"
            )
        
        # Generate new API key
        api_key = encryption_manager.generate_api_key()
        
        # Log the API key generation
        event = SecurityEvent(
            event_type="api_key_generated",
            user_id=current_user.get("user_id"),
            ip_address="System",
            user_agent="System",
            timestamp=datetime.now(),
            details={
                "generated_by": current_user.get("user_id"),
                "key_length": len(api_key)
            },
            severity="INFO"
        )
        enhanced_security.security_monitor.log_security_event(event)
        
        return {
            "api_key": api_key,
            "message": "API key generated successfully",
            "warning": "Store this key securely and do not share it"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to generate API key: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate API key"
        )
