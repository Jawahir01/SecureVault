from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.orm import Session
from datetime import datetime
from app.database import get_db
from app.models import User, Secret, AccessLog, AuditLog
from app.schemas import (
    SecretCreate,
    SecretResponse,
    SecretValueResponse,
    SecretUpdate,
    SecretListResponse,
)
from app.security.deps import get_current_active_user
from app.security.encryption import EncryptionService
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/secrets", tags=["Secrets"])


def _log_access(
    db: Session,
    secret_id: str,
    user_id: str,
    action: str,
    request: Request,
    success: bool = True,
):
    """Log access to a secret."""
    access_log = AccessLog(
        secret_id=secret_id,
        user_id=user_id,
        action=action,
        ip_address=request.client.host if request.client else "unknown",
        user_agent=request.headers.get("user-agent"),
        success=success,
    )
    db.add(access_log)
    db.commit()


def _log_audit(
    db: Session,
    user_id: str,
    action: str,
    resource: str,
    resource_id: str,
    request: Request,
    changes: str = None,
):
    """Log audit trail."""
    audit_log = AuditLog(
        user_id=user_id,
        action=action,
        resource=resource,
        resource_id=resource_id,
        changes=changes,
        ip_address=request.client.host if request.client else "unknown",
        user_agent=request.headers.get("user-agent"),
    )
    db.add(audit_log)
    db.commit()


@router.post("", response_model=SecretResponse, status_code=status.HTTP_201_CREATED)
async def create_secret(
    secret_data: SecretCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    request: Request = None,
):
    """
    Create a new secret.

    Security:
    - Secret value is encrypted with AES-256
    - Only owner can access
    - All access is logged
    """
    # Encrypt the secret value
    encryption_service = EncryptionService()
    encrypted_value = encryption_service.encrypt(secret_data.value)

    # Create secret
    secret = Secret(
        owner_id=current_user.id,
        name=secret_data.name,
        encrypted_value=encrypted_value,
        secret_type=secret_data.secret_type,
        description=secret_data.description,
    )

    db.add(secret)
    db.commit()
    db.refresh(secret)

    # Log access
    _log_access(db, secret.id, current_user.id, "create", request)
    _log_audit(db, current_user.id, "CREATE", "secrets", secret.id, request)

    logger.info(f"Secret created: {secret.id} by {current_user.username}")

    return secret


@router.get("", response_model=SecretListResponse)
async def list_secrets(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    secret_type: str = Query(None),
    request: Request = None,
):
    """
    List all secrets owned by current user.

    Pagination:
    - page: 1-based page number
    - per_page: items per page (max 100)
    """
    query = db.query(Secret).filter(Secret.owner_id == current_user.id)

    # Filter by type if provided
    if secret_type:
        query = query.filter(Secret.secret_type == secret_type)

    total = query.count()

    secrets = query.offset((page - 1) * per_page).limit(per_page).all()

    logger.info(f"User {current_user.username} listed {len(secrets)} secrets")

    return SecretListResponse(
        total=total,
        page=page,
        per_page=per_page,
        secrets=secrets,
    )


@router.get("/{secret_id}", response_model=SecretValueResponse)
async def get_secret(
    secret_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    request: Request = None,
):
    """
    Get a specific secret with decrypted value.

    Security:
    - Only owner can access
    - Access is logged for audit trail
    """
    secret = db.query(Secret).filter(Secret.id == secret_id).first()

    if not secret:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Secret not found",
        )

    # Check ownership
    if secret.owner_id != current_user.id:
        # Don't reveal if secret exists
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Secret not found",
        )

    # Decrypt value
    try:
        encryption_service = EncryptionService()
        decrypted_value = encryption_service.decrypt(secret.encrypted_value)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to decrypt secret",
        )

    # Update accessed_at
    secret.accessed_at = datetime.utcnow()
    db.commit()

    # Log access
    _log_access(db, secret.id, current_user.id, "read", request)

    logger.info(f"Secret accessed: {secret_id} by {current_user.username}")

    return SecretValueResponse(
        id=secret.id,
        name=secret.name,
        secret_type=secret.secret_type,
        description=secret.description,
        created_at=secret.created_at,
        updated_at=secret.updated_at,
        accessed_at=secret.accessed_at,
        value=decrypted_value,
    )


@router.put("/{secret_id}", response_model=SecretResponse)
async def update_secret(
    secret_id: str,
    update_data: SecretUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    request: Request = None,
):
    """
    Update a secret.

    Security:
    - Only owner can update
    - Changes are audited
    """
    secret = db.query(Secret).filter(Secret.id == secret_id).first()

    if not secret:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Secret not found",
        )

    if secret.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Secret not found",
        )

    # Track changes for audit
    changes = {}

    if update_data.name is not None:
        changes["name"] = {"old": secret.name, "new": update_data.name}
        secret.name = update_data.name

    if update_data.value is not None:
        changes["value"] = "updated"
        encryption_service = EncryptionService()
        secret.encrypted_value = encryption_service.encrypt(update_data.value)

    if update_data.description is not None:
        changes["description"] = {
            "old": secret.description,
            "new": update_data.description,
        }
        secret.description = update_data.description

    if update_data.secret_type is not None:
        changes["secret_type"] = {
            "old": secret.secret_type,
            "new": update_data.secret_type,
        }
        secret.secret_type = update_data.secret_type

    secret.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(secret)

    # Log
    _log_access(db, secret.id, current_user.id, "update", request)
    import json

    _log_audit(
        db,
        current_user.id,
        "UPDATE",
        "secrets",
        secret_id,
        request,
        json.dumps(changes),
    )

    logger.info(f"Secret updated: {secret_id} by {current_user.username}")

    return secret


@router.delete("/{secret_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_secret(
    secret_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    request: Request = None,
):
    """
    Delete a secret.

    Security:
    - Only owner can delete
    - Deletion is logged
    """
    secret = db.query(Secret).filter(Secret.id == secret_id).first()

    if not secret:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Secret not found",
        )

    if secret.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Secret not found",
        )

    db.delete(secret)
    db.commit()

    # Log
    _log_audit(db, current_user.id, "DELETE", "secrets", secret_id, request)

    logger.info(f"Secret deleted: {secret_id} by {current_user.username}")


@router.get("/audit-logs/", tags=["Audit"])
async def get_audit_logs(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
):
    """
    Get audit logs (admin only view).
    """
    # For simplicity, return user's own audit logs
    # In production, only admins should see all logs

    query = db.query(AuditLog).filter(AuditLog.user_id == current_user.id)
    total = query.count()

    logs = (
        query.order_by(AuditLog.timestamp.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )

    return {
        "total": total,
        "page": page,
        "per_page": per_page,
        "logs": logs,
    }
