import pytest
from fastapi import status
from app.security.encryption import EncryptionService

class TestSecretsAPI:
    """Test secrets management API."""
    
    def test_create_secret(self, client, auth_headers, db):
        """Test creating a secret."""
        secret_data = {
            "name": "api_key",
            "value": "sk_test_1234567890",
            "secret_type": "api_key",
            "description": "Stripe API key"
        }
        
        response = client.post(
            "/api/v1/secrets",
            json=secret_data,
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["name"] == secret_data["name"]
        assert data["secret_type"] == secret_data["secret_type"]
        assert "value" not in data  # Value should not be in response
        assert data["description"] == secret_data["description"]
    
    def test_create_secret_without_auth(self, client):
        """Test creating secret without authentication."""
        secret_data = {
            "name": "api_key",
            "value": "secret_value",
            "secret_type": "api_key",
        }
        
        response = client.post("/api/v1/secrets", json=secret_data)
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_list_secrets(self, client, auth_headers, test_secret):
        """Test listing secrets."""
        response = client.get(
            "/api/v1/secrets",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total"] >= 1
        assert len(data["secrets"]) > 0
    
    def test_list_secrets_empty(self, client, auth_headers):
        """Test listing secrets when none exist."""
        response = client.get(
            "/api/v1/secrets",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total"] == 0
    
    def test_get_secret(self, client, auth_headers, test_secret):
        """Test retrieving a secret with decrypted value."""
        response = client.get(
            f"/api/v1/secrets/{test_secret.id}",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == test_secret.id
        assert data["name"] == test_secret.name
        assert data["value"] == "super_secret_api_key_12345"  # Decrypted
    
    def test_get_secret_not_found(self, client, auth_headers):
        """Test getting nonexistent secret."""
        response = client.get(
            "/api/v1/secrets/nonexistent_id",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_get_secret_unauthorized(self, client, auth_headers, test_secret, test_user_data, db):
        """Test getting another user's secret."""
        # Create another user
        from app.models import User
        from app.security.auth import auth_service
        
        other_user = User(
            email="other@example.com",
            username="otheruser",
            hashed_password=auth_service.hash_password("Password123!@#"),
            is_active=True,
        )
        db.add(other_user)
        db.commit()
        
        # Try to access first user's secret with second user's token
        other_token = auth_service.create_access_token(
            data={"sub": other_user.id, "email": other_user.email}
        )
        other_headers = {"Authorization": f"Bearer {other_token}"}
        
        response = client.get(
            f"/api/v1/secrets/{test_secret.id}",
            headers=other_headers
        )
        
        # Should return 404 (doesn't reveal if secret exists for other user)
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_update_secret(self, client, auth_headers, test_secret):
        """Test updating a secret."""
        update_data = {
            "name": "updated_api_key",
            "value": "new_secret_value_xyz"
        }
        
        response = client.put(
            f"/api/v1/secrets/{test_secret.id}",
            json=update_data,
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["name"] == update_data["name"]
    
    def test_delete_secret(self, client, auth_headers, test_secret):
        """Test deleting a secret."""
        response = client.delete(
            f"/api/v1/secrets/{test_secret.id}",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
        
        # Verify secret is deleted
        response = client.get(
            f"/api/v1/secrets/{test_secret.id}",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_pagination(self, client, auth_headers, test_user, db):
        """Test pagination."""
        from app.models import Secret
        
        # Create multiple secrets
        for i in range(15):
            secret = Secret(
                owner_id=test_user.id,
                name=f"secret_{i}",
                encrypted_value=EncryptionService.encrypt(f"value_{i}"),
                secret_type="generic",
            )
            db.add(secret)
        db.commit()
        
        # Test first page
        response = client.get(
            "/api/v1/secrets?page=1&per_page=10",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total"] == 15
        assert len(data["secrets"]) == 10
        
        # Test second page
        response = client.get(
            "/api/v1/secrets?page=2&per_page=10",
            headers=auth_headers
        )
        data = response.json()
        assert len(data["secrets"]) == 5

class TestHealthCheck:
    """Test health check endpoint."""
    
    def test_health_check(self, client):
        """Test health endpoint."""
        response = client.get("/health")
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["status"] == "healthy"
    
    def test_root_endpoint(self, client):
        """Test root endpoint."""
        response = client.get("/")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "name" in data
        assert "version" in data