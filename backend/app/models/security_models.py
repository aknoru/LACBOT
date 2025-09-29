"""
Security-related database models for LACBOT
"""

from sqlalchemy import Column, String, DateTime, Text, Integer, Boolean, JSON, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
import uuid

Base = declarative_base()

class SecurityEvent(Base):
    """Security event logging table"""
    __tablename__ = "security_events"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_type = Column(String(100), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    ip_address = Column(String(45), nullable=False, index=True)  # IPv6 compatible
    user_agent = Column(Text, nullable=False)
    timestamp = Column(DateTime(timezone=True), default=func.now(), index=True)
    details = Column(JSON, nullable=False)
    severity = Column(String(20), nullable=False, index=True)  # INFO, WARNING, ERROR, CRITICAL
    resolved = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=func.now())
    
    def __repr__(self):
        return f"<SecurityEvent(id={self.id}, type={self.event_type}, severity={self.severity})>"

class RateLimitLog(Base):
    """Rate limiting logs table"""
    __tablename__ = "rate_limit_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    identifier = Column(String(255), nullable=False, index=True)  # IP or User ID
    identifier_type = Column(String(20), nullable=False)  # ip or user
    request_count = Column(Integer, nullable=False)
    window_start = Column(DateTime(timezone=True), nullable=False, index=True)
    window_end = Column(DateTime(timezone=True), nullable=False)
    limit_exceeded = Column(Boolean, default=False)
    penalty_applied = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=func.now())

class BlockedIP(Base):
    """Blocked IP addresses table"""
    __tablename__ = "blocked_ips"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ip_address = Column(String(45), nullable=False, unique=True, index=True)
    blocked_by = Column(UUID(as_uuid=True), nullable=False)
    reason = Column(Text, nullable=False)
    blocked_at = Column(DateTime(timezone=True), default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=True, index=True)
    unblocked_at = Column(DateTime(timezone=True), nullable=True)
    unblocked_by = Column(UUID(as_uuid=True), nullable=True)

class UserSession(Base):
    """User session tracking table"""
    __tablename__ = "user_sessions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    session_token = Column(String(255), nullable=False, unique=True, index=True)
    ip_address = Column(String(45), nullable=False)
    user_agent = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), default=func.now())
    last_activity = Column(DateTime(timezone=True), default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
    is_active = Column(Boolean, default=True, index=True)
    logout_reason = Column(String(100), nullable=True)  # user_logout, timeout, admin_logout

class PasswordHistory(Base):
    """Password history for security compliance"""
    __tablename__ = "password_history"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    salt = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), default=func.now())
    is_current = Column(Boolean, default=False, index=True)

class FailedLoginAttempt(Base):
    """Failed login attempt tracking"""
    __tablename__ = "failed_login_attempts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), nullable=False, index=True)
    ip_address = Column(String(45), nullable=False, index=True)
    user_agent = Column(Text, nullable=False)
    attempt_time = Column(DateTime(timezone=True), default=func.now(), index=True)
    failure_reason = Column(String(100), nullable=False)  # invalid_password, user_not_found, account_locked
    is_blocked = Column(Boolean, default=False)

class SecurityAuditLog(Base):
    """Comprehensive security audit log"""
    __tablename__ = "security_audit_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    action = Column(String(100), nullable=False, index=True)  # login, logout, create_user, delete_user, etc.
    resource_type = Column(String(50), nullable=True)  # user, document, faq, etc.
    resource_id = Column(UUID(as_uuid=True), nullable=True)
    ip_address = Column(String(45), nullable=False, index=True)
    user_agent = Column(Text, nullable=False)
    request_data = Column(JSON, nullable=True)
    response_data = Column(JSON, nullable=True)
    status_code = Column(Integer, nullable=False)
    timestamp = Column(DateTime(timezone=True), default=func.now(), index=True)
    audit_hash = Column(String(64), nullable=False, unique=True, index=True)
    risk_score = Column(Float, default=0.0, index=True)  # 0-100 risk assessment

class EncryptionKey(Base):
    """Encryption key management"""
    __tablename__ = "encryption_keys"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    key_type = Column(String(50), nullable=False)  # symmetric, asymmetric, session
    key_name = Column(String(100), nullable=False, unique=True, index=True)
    key_data = Column(Text, nullable=False)  # Encrypted key data
    algorithm = Column(String(50), nullable=False)  # AES-256-GCM, RSA-2048, etc.
    created_at = Column(DateTime(timezone=True), default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=True, index=True)
    created_by = Column(UUID(as_uuid=True), nullable=False)
    last_rotated = Column(DateTime(timezone=True), nullable=True)

class DataClassification(Base):
    """Data classification and handling rules"""
    __tablename__ = "data_classifications"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    table_name = Column(String(100), nullable=False, index=True)
    column_name = Column(String(100), nullable=False)
    classification = Column(String(20), nullable=False)  # public, internal, confidential, restricted
    encryption_required = Column(Boolean, default=False)
    retention_days = Column(Integer, nullable=True)
    access_level = Column(String(50), nullable=False)  # public, user, volunteer, superuser
    created_at = Column(DateTime(timezone=True), default=func.now())
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())

class SecurityPolicy(Base):
    """Security policies and rules"""
    __tablename__ = "security_policies"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    policy_name = Column(String(100), nullable=False, unique=True, index=True)
    policy_type = Column(String(50), nullable=False)  # password, session, rate_limit, encryption
    policy_data = Column(JSON, nullable=False)
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime(timezone=True), default=func.now())
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())
    created_by = Column(UUID(as_uuid=True), nullable=False)

class ThreatIntelligence(Base):
    """Threat intelligence and indicators"""
    __tablename__ = "threat_intelligence"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    indicator_type = Column(String(50), nullable=False)  # ip, domain, email, hash
    indicator_value = Column(String(500), nullable=False, index=True)
    threat_type = Column(String(100), nullable=False)  # malware, phishing, botnet, etc.
    severity = Column(String(20), nullable=False)  # low, medium, high, critical
    confidence = Column(Float, nullable=False)  # 0.0-1.0
    source = Column(String(100), nullable=False)  # internal, external_feed, manual
    first_seen = Column(DateTime(timezone=True), default=func.now())
    last_seen = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=True, index=True)
    metadata = Column(JSON, nullable=True)

class ComplianceLog(Base):
    """Compliance and regulatory logging"""
    __tablename__ = "compliance_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    regulation = Column(String(50), nullable=False)  # GDPR, HIPAA, SOX, etc.
    action = Column(String(100), nullable=False)  # data_access, data_deletion, consent_given, etc.
    user_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    data_subject_id = Column(UUID(as_uuid=True), nullable=True)  # For GDPR compliance
    ip_address = Column(String(45), nullable=False)
    timestamp = Column(DateTime(timezone=True), default=func.now(), index=True)
    details = Column(JSON, nullable=False)
    retention_until = Column(DateTime(timezone=True), nullable=True)
    is_compliant = Column(Boolean, default=True, index=True)

class SecurityMetrics(Base):
    """Security metrics and KPIs"""
    __tablename__ = "security_metrics"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    metric_name = Column(String(100), nullable=False, index=True)
    metric_value = Column(Float, nullable=False)
    metric_type = Column(String(50), nullable=False)  # counter, gauge, histogram
    timestamp = Column(DateTime(timezone=True), default=func.now(), index=True)
    tags = Column(JSON, nullable=True)
    metadata = Column(JSON, nullable=True)

class VulnerabilityScan(Base):
    """Vulnerability scan results"""
    __tablename__ = "vulnerability_scans"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    scan_type = Column(String(50), nullable=False)  # dependency, code, infrastructure
    scan_target = Column(String(200), nullable=False)
    vulnerability_id = Column(String(100), nullable=False, index=True)
    severity = Column(String(20), nullable=False, index=True)  # low, medium, high, critical
    description = Column(Text, nullable=False)
    cve_id = Column(String(50), nullable=True, index=True)
    cvss_score = Column(Float, nullable=True)
    status = Column(String(20), default="open", index=True)  # open, fixed, false_positive, accepted_risk
    scan_date = Column(DateTime(timezone=True), default=func.now(), index=True)
    fixed_date = Column(DateTime(timezone=True), nullable=True)
    assigned_to = Column(UUID(as_uuid=True), nullable=True)
    remediation_notes = Column(Text, nullable=True)
