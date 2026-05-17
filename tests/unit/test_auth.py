import pytest
from fastapi import status
from app.security.auth import auth_service
from app.models import User
import jwt

class TestAuthService:
    """Test authentication service."""
    
    def test_hash_password(self):
        """Test password hashing."""
        password = "SecurePassword123!@#"
        hashed = auth_service.hash_password(password)
        
        assert hashed != password
        assert auth_service.verify_password(password, hashed)
    
    def test_verify_password_wrong(self):
        """Test password verification fails for wrong password."""
        password = "SecurePassword123!@#"
        hashed = auth_service.hash_password(password)
        
        assert not auth_service.verify_password("WrongPassword", hashed)
    
    def test_create_access_token(self):
        """Test access token creation."""
        data = {"sub": "user123", "email": "test@example.com"}
        token = auth_service.create_access_token(data)
        
        assert token
        assert isinstance(token, str)
        
        # Decode and verify
        payload = auth_service.verify_token(token)
        assert payload["sub"] == "user123"
        assert payload["email"] == "test@example.com"
    
    def test_create_refresh_token(self):
        """Test refresh token creation."""
        data = {"sub": "user123"}
        token = auth_service.create_refresh_token(data)
        
        assert token
        
        payload = auth_service.verify_token(token)
        assert payload["sub"] == "user123"
        assert payload["type"] == "refresh"
    
    def test_verify_invalid_token(self):
        """Test invalid token verification raises error."""
        with pytest.raises(ValueError):
            auth_service.verify_token("invalid.token.here")
    
    def test_verify_expired_token(self):
        """Test expired token raises error."""
        from datetime import datetime, timedelta
        from app.config import get_settings
        
        settings = get_settings()
        
        # Create token with past expiration
        data = {"sub": "user123", "exp": datetime.utcnow() - timedelta(hours=1)}
        token = jwt.encode(data, settings.secret_key, algorithm=settings.algorithm)
        
        with pytest.raises(ValueError, match="expired"):
            auth_service.verify_token(token)

class TestAuthEndpoints:
    """Test authentication endpoints."""
    
    def test_register_user(self, client, test_user_data):
        """Test user registration."""
        response = client.post("/api/v1/auth/register", json=test_user_data)
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["email"] == test_user_data["email"]
        assert data["username"] == test_user_data["username"]
        assert "hashed_password" not in data
    
    def test_register_duplicate_email(self, client, test_user_data, test_user):
        """Test registration fails with duplicate email."""
        response = client.post("/api/v1/auth/register", json=test_user_data)
        assert response.status_code == status.HTTP_409_CONFLICT
    
    def test_register_weak_password(self, client):
        """Test registration fails with weak password."""
        weak_user = {
            "email": "test@example.com",
            "username": "testuser",
            "password": "weak"  # Too short
        }
        response = client.post("/api/v1/auth/register", json=weak_user)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_login_success(self, client, test_user, test_user_data):
        """Test successful login."""
        credentials = {
            "username": test_user_data["username"],
            "password": test_user_data["password"]
        }
        response = client.post("/api/v1/auth/login", json=credentials)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
    
    def test_login_invalid_credentials(self, client, test_user):
        """Test login with invalid credentials."""
        credentials = {
            "username": "testuser",
            "password": "WrongPassword123!@#"
        }
        response = client.post("/api/v1/auth/login", json=credentials)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_login_nonexistent_user(self, client):
        """Test login with nonexistent user."""
        credentials = {
            "username": "nonexistent",
            "password": "Password123!@#"
        }
        response = client.post("/api/v1/auth/login", json=credentials)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_refresh_token(self, client, test_user, auth_headers):
        """Test token refresh."""
        # First login to get refresh token
        credentials = {
            "username": test_user.username,
            "password": "SecurePassword123!@#"
        }
        login_response = client.post("/api/v1/auth/login", json=credentials)
        refresh_token = login_response.json()["refresh_token"]
        
        # Refresh the token
        response = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token}
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data