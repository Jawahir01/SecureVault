from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Index, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from app.database import Base

class Secret(Base):
    """Encrypted secret storage."""
    __tablename__ = "secrets"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    owner_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    encrypted_value = Column(Text, nullable=False)  # AES-256 encrypted
    secret_type = Column(String(50), default="generic")  # api_key, password, database_url, etc.
    description = Column(Text, nullable=True)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    accessed_at = Column(DateTime, nullable=True)  # Track when secret was last accessed
    
    # Relationships
    owner = relationship("User", back_populates="secrets")
    access_logs = relationship("AccessLog", back_populates="secret", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_secret_owner', 'owner_id'),
        Index('idx_secret_name_owner', 'name', 'owner_id'),
    )

class AccessLog(Base):
    """Log every access to secrets for audit purposes."""
    __tablename__ = "access_logs"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    secret_id = Column(String(36), ForeignKey("secrets.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    action = Column(String(50), nullable=False)  # read, create, update, delete
    ip_address = Column(String(45), nullable=False)  # IPv4 or IPv6
    user_agent = Column(String(500), nullable=True)
    success = Column(Boolean, default=True, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    secret = relationship("Secret", back_populates="access_logs")
    user = relationship("User")
    
    __table_args__ = (
        Index('idx_access_log_secret', 'secret_id'),
        Index('idx_access_log_user', 'user_id'),
        Index('idx_access_log_timestamp', 'timestamp'),
    )

class AuditLog(Base):
    """High-level audit trail of all API actions."""
    __tablename__ = "audit_logs"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    action = Column(String(255), nullable=False)
    resource = Column(String(100), nullable=False)  # users, secrets, tokens, etc.
    resource_id = Column(String(36), nullable=True)
    changes = Column(Text, nullable=True)  # JSON string of what changed
    ip_address = Column(String(45), nullable=False)
    user_agent = Column(String(500), nullable=True)
    status_code = Column(String(10), nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    user = relationship("User", back_populates="audit_logs")
    
    __table_args__ = (
        Index('idx_audit_log_user', 'user_id'),
        Index('idx_audit_log_timestamp', 'timestamp'),
        Index('idx_audit_log_resource', 'resource', 'resource_id'),
    )
