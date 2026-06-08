import os
import uuid
import pytest
import requests  # type: ignore[import]

BASE_URL = os.getenv("SECUREVAULT_URL", "http://localhost:8000")

# Skip all tests in this module if SECUREVAULT_URL is not explicitly set (CI environment)
pytestmark = pytest.mark.skipif(
    "SECUREVAULT_URL" not in os.environ,
    reason="Integration tests require a running SecureVault server",
)


def random_email():
    return f"test-{uuid.uuid4().hex[:8]}@example.com"


@pytest.fixture
def user_credentials():
    return {"email": random_email(), "password": "StrongPassw0rd!"}


def test_register_user(user_credentials: dict[str, str]):
    response = requests.post(f"{BASE_URL}/auth/register", json=user_credentials)
    assert response.status_code == 201

    data = response.json()
    assert data.get("email") == user_credentials["email"]
    assert "id" in data


def test_login_user(user_credentials: dict[str, str]):
    register_response = requests.post(
        f"{BASE_URL}/auth/register", json=user_credentials
    )
    assert register_response.status_code == 201

    login_response = requests.post(
        f"{BASE_URL}/auth/login",
        data={
            "username": user_credentials["email"],
            "password": user_credentials["password"],
        },
    )
    assert login_response.status_code == 200

    data = login_response.json()
    assert "access_token" in data
    assert data.get("token_type", "").lower() == "bearer"


def test_protected_route_requires_auth():
    response = requests.get(f"{BASE_URL}/vault")
    assert response.status_code in (401, 403)


def test_access_protected_route_after_login(user_credentials: dict[str, str]):
    register_response = requests.post(
        f"{BASE_URL}/auth/register", json=user_credentials
    )
    assert register_response.status_code == 201

    login_response = requests.post(
        f"{BASE_URL}/auth/login",
        data={
            "username": user_credentials["email"],
            "password": user_credentials["password"],
        },
    )
    assert login_response.status_code == 200

    token = login_response.json().get("access_token")
    assert token

    vault_response = requests.get(
        f"{BASE_URL}/vault",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert vault_response.status_code == 200
