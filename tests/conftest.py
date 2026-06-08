import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
import sys
import os

# Set test database URL before importing app to avoid config errors
os.environ.setdefault("DATABASE_URL", "sqlite:///./test.db")
os.environ.setdefault("SECRET_KEY", "test-secret-key")
os.environ.setdefault("ENCRYPTION_KEY", "test-encryption-key-1234567890ab")

# Add the parent directory to Python path so 'app' module can be found
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app
from app.database import get_db, Base
from app.models import User, Secret, RefreshToken
from app.security.auth import AuthService
from app.security.encryption import EncryptionService

# Use in-memory SQLite for testing
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db():
    """Create a fresh database for each test."""
    Base.metadata.create_all(bind=engine)
    db_session = TestingSessionLocal()
    
    yield db_session
    
    db_session.close()
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def client(db: Session):
    """Create test client with test database."""
    def override_get_db():
        try:
            yield db
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()

@pytest.fixture
def test_user_data():
    """Test user data."""
    return {
        "email": "test@example.com",
        "username": "testuser",
        "password": "SecurePassword123!@#"
    }

@pytest.fixture
def test_user(db: Session, test_user_data):
    """Create a test user in database."""
    user = User(
        email=test_user_data["email"],
        username=test_user_data["username"],
        hashed_password=AuthService.hash_password(test_user_data["password"]),
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@pytest.fixture
def test_token(db: Session, test_user):
    """Create a JWT token for test user."""
    access_token = AuthService.create_access_token(
        data={"sub": test_user.id, "email": test_user.email}
    )
    return access_token

@pytest.fixture
def auth_headers(test_token):
    """Authorization headers with token."""
    return {"Authorization": f"Bearer {test_token}"}

@pytest.fixture
def test_secret(db: Session, test_user):
    """Create a test secret."""
    secret = Secret(
        owner_id=test_user.id,
        name="test_api_key",
        encrypted_value=EncryptionService.encrypt("super_secret_api_key_12345"),
        secret_type="api_key",
        description="Test API key",
    )
    db.add(secret)
    db.commit()
    db.refresh(secret)
    return secret