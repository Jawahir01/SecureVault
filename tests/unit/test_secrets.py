import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
from SecureVault.secrets_manager import (
    SecretsManager,
    SecretNotFoundError,
    SecretExpiredError,
)


class TestSecretsManager:
    """Test cases for SecretsManager class."""

    @pytest.fixture
    def secrets_manager(self):
        """Create a SecretsManager instance for testing."""
        return SecretsManager()

    def test_store_secret(self, secrets_manager):
        """Test storing a secret."""
        key = "test_key"
        value = "test_secret_value"
        secrets_manager.store(key, value)
        assert secrets_manager.retrieve(key) == value

    def test_retrieve_existing_secret(self, secrets_manager):
        """Test retrieving an existing secret."""
        key = "api_key"
        value = "secret123"
        secrets_manager.store(key, value)
        assert secrets_manager.retrieve(key) == value

    def test_retrieve_nonexistent_secret(self, secrets_manager):
        """Test retrieving a secret that doesn't exist."""
        with pytest.raises(SecretNotFoundError):
            secrets_manager.retrieve("nonexistent_key")

    def test_delete_secret(self, secrets_manager):
        """Test deleting a secret."""
        key = "temp_key"
        value = "temporary_secret"
        secrets_manager.store(key, value)
        secrets_manager.delete(key)
        with pytest.raises(SecretNotFoundError):
            secrets_manager.retrieve(key)

    def test_secret_expiration(self, secrets_manager):
        """Test that expired secrets cannot be retrieved."""
        key = "expiring_key"
        value = "expiring_secret"
        ttl = 1  # 1 second
        secrets_manager.store(key, value, ttl=ttl)

        # Wait for expiration
        import time

        time.sleep(ttl + 0.1)

        with pytest.raises(SecretExpiredError):
            secrets_manager.retrieve(key)

    def test_store_secret_with_metadata(self, secrets_manager):
        """Test storing a secret with metadata."""
        key = "metadata_key"
        value = "secret_with_metadata"
        metadata = {"environment": "production", "version": 1}
        secrets_manager.store(key, value, metadata=metadata)

        secret = secrets_manager.retrieve(key, include_metadata=True)
        assert secret["value"] == value
        assert secret["metadata"] == metadata

    def test_list_secrets(self, secrets_manager):
        """Test listing all secret keys."""
        secrets_manager.store("key1", "value1")
        secrets_manager.store("key2", "value2")
        secrets_manager.store("key3", "value3")

        keys = secrets_manager.list_keys()
        assert len(keys) == 3
        assert "key1" in keys
        assert "key2" in keys
        assert "key3" in keys

    def test_update_secret(self, secrets_manager):
        """Test updating an existing secret."""
        key = "update_key"
        initial_value = "initial_secret"
        updated_value = "updated_secret"

        secrets_manager.store(key, initial_value)
        secrets_manager.store(key, updated_value)

        assert secrets_manager.retrieve(key) == updated_value

    def test_secret_encryption(self, secrets_manager):
        """Test that secrets are encrypted."""
        key = "encryption_test"
        value = "sensitive_data"
        secrets_manager.store(key, value)

        # Access internal storage to verify encryption
        stored = secrets_manager._storage[key]
        assert stored["value"] != value  # Value should be encrypted

    def test_clear_all_secrets(self, secrets_manager):
        """Test clearing all secrets."""
        secrets_manager.store("key1", "value1")
        secrets_manager.store("key2", "value2")
        secrets_manager.store("key3", "value3")

        secrets_manager.clear()
        keys = secrets_manager.list_keys()
        assert len(keys) == 0

    def test_secret_access_audit_log(self, secrets_manager):
        """Test that secret accesses are logged."""
        key = "audit_key"
        value = "audit_secret"
        secrets_manager.store(key, value)
        secrets_manager.retrieve(key)

        audit_log = secrets_manager.get_audit_log(key)
        assert len(audit_log) > 0
        assert any(log["action"] == "retrieve" for log in audit_log)

    def test_rotate_secret(self, secrets_manager):
        """Test rotating a secret."""
        key = "rotation_key"
        old_value = "old_secret"
        new_value = "new_secret"

        secrets_manager.store(key, old_value)
        secrets_manager.rotate(key, new_value)

        assert secrets_manager.retrieve(key) == new_value
        history = secrets_manager.get_secret_history(key)
        assert len(history) >= 2


class TestSecretsManagerExceptions:
    """Test cases for SecretsManager exceptions."""

    def test_secret_not_found_error_message(self):
        """Test SecretNotFoundError message."""
        error = SecretNotFoundError("test_key")
        assert "test_key" in str(error)

    def test_secret_expired_error_message(self):
        """Test SecretExpiredError message."""
        error = SecretExpiredError("expired_key")
        assert "expired_key" in str(error)


class TestSecretsManagerIntegration:
    """Integration tests for SecretsManager."""

    def test_workflow_create_retrieve_update_delete(self):
        """Test complete workflow: create, retrieve, update, delete."""
        manager = SecretsManager()

        # Create
        manager.store("db_password", "initial_password")
        assert manager.retrieve("db_password") == "initial_password"

        # Update
        manager.store("db_password", "updated_password")
        assert manager.retrieve("db_password") == "updated_password"

        # Delete
        manager.delete("db_password")
        with pytest.raises(SecretNotFoundError):
            manager.retrieve("db_password")

    def test_multiple_secrets_isolation(self):
        """Test that multiple secrets are properly isolated."""
        manager = SecretsManager()

        manager.store("secret1", "value1")
        manager.store("secret2", "value2")
        manager.store("secret3", "value3")

        assert manager.retrieve("secret1") == "value1"
        assert manager.retrieve("secret2") == "value2"
        assert manager.retrieve("secret3") == "value3"
