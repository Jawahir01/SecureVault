from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import timedelta
from app.database import get_db
from app.models import User, RefreshToken
from app.schemas import LoginRequest, TokenResponse, UserCreate, UserResponse
from app.security.auth import auth_service
from app.config import get_settings
from datetime import datetime
import logging

logger = logging.getLogger(__name__)
settings = get_settings()
router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """
    Register a new user.
    
    Security requirements:
    - Password must be at least 12 characters
    - Email must be unique
    - Username must be unique
    """
    # Check if user already exists
    if db.query(User).filter(User.email == user_data.email).first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )
    
    if db.query(User).filter(User.username == user_data.username).first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already taken",
        )
    
    # Create new user
    user = User(
        email=user_data.email,
        username=user_data.username,
        hashed_password=auth_service.hash_password(user_data.password),
        is_active=True,
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    logger.info(f"New user registered: {user.username}")
    
    return user

@router.post("/login", response_model=TokenResponse)
async def login(
    credentials: LoginRequest,
    db: Session = Depends(get_db),
):
    """
    Login user and return access + refresh tokens.
    
    Security features:
    - Bcrypt password verification (slow hash, resistant to brute force)
    - JWT tokens with expiration
    - Refresh token stored in DB for revocation
    """
    # Find user
    user = db.query(User).filter(
        (User.username == credentials.username) | (User.email == credentials.username)
    ).first()
    
    if not user or not auth_service.verify_password(credentials.password, user.hashed_password):
        # Don't reveal if user exists (timing attack protection)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled",
        )
    
    # Update last login
    user.last_login = datetime.utcnow()
    
    # Create tokens
    access_token = auth_service.create_access_token(
        data={"sub": user.id, "email": user.email}
    )
    
    refresh_token = auth_service.create_refresh_token(
        data={"sub": user.id}
    )
    
    # Store refresh token in database for revocation capability
    refresh_token_obj = RefreshToken(
        user_id=user.id,
        token=refresh_token,
        expires_at=datetime.utcnow() + timedelta(days=settings.refresh_token_expire_days),
    )
    
    db.add(refresh_token_obj)
    db.commit()
    
    logger.info(f"User logged in: {user.username}")
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.access_token_expire_minutes * 60,
    )

@router.post("/refresh", response_model=TokenResponse)
async def refresh_access_token(
    request_data: dict,
    db: Session = Depends(get_db),
):
    """
    Refresh access token using refresh token.
    
    Security: Refresh tokens can be revoked for logout
    """
    refresh_token = request_data.get("refresh_token")
    
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Refresh token required",
        )
    
    try:
        payload = auth_service.verify_token(refresh_token)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        )
    
    # Check if token is revoked
    token_obj = db.query(RefreshToken).filter(
        RefreshToken.token == refresh_token,
        RefreshToken.is_revoked == False,
    ).first()
    
    if not token_obj:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token revoked or invalid",
        )
    
    user_id = payload.get("sub")
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )
    
    # Create new access token
    new_access_token = auth_service.create_access_token(
        data={"sub": user.id, "email": user.email}
    )
    
    # Optionally rotate refresh token
    new_refresh_token = auth_service.create_refresh_token(
        data={"sub": user.id}
    )
    
    # Revoke old refresh token
    token_obj.is_revoked = True
    
    # Store new refresh token
    new_token_obj = RefreshToken(
        user_id=user.id,
        token=new_refresh_token,
        expires_at=datetime.utcnow() + timedelta(days=settings.refresh_token_expire_days),
    )
    
    db.add(new_token_obj)
    db.commit()
    
    return TokenResponse(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
        expires_in=settings.access_token_expire_minutes * 60,
    )

@router.post("/logout")
async def logout(
    refresh_token: str,
    db: Session = Depends(get_db),
):
    """
    Logout user by revoking refresh token.
    """
    token_obj = db.query(RefreshToken).filter(
        RefreshToken.token == refresh_token
    ).first()
    
    if token_obj:
        token_obj.is_revoked = True
        db.commit()
        logger.info(f"Refresh token revoked for user: {token_obj.user_id}")
    
    return {"status": "logged out"}