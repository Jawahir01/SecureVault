"""Secrets management module for SecureVault."""

import time
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
from cryptography.fernet import Fernet
import os


class SecretNotFoundError(Exception):
    """Raised when a secret is not found."""
    
    def __init__(self, key: str):
        self.key = key
        super().__init__(f"Secret with key '{key}' not found")


class SecretExpiredError(Exception):
    """Raised when a secret has expired."""
    
    def __init__(self, key: str):
        self.key = key
        super().__init__(f"Secret with key '{key}' has expired")


class SecretsManager:
    """Manages secure storage and retrieval of secrets."""
    
    def __init__(self):
        """Initialize the SecretsManager with encryption."""
        # Generate or load encryption key
        self._key = Fernet.generate_key()
        self._cipher = Fernet(self._key)
        self._storage: Dict[str, Dict[str, Any]] = {}
        self._audit_log: Dict[str, List[Dict[str, Any]]] = {}
    
    def store(self, key: str, value: str, ttl: Optional[int] = None, metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Store a secret with optional TTL and metadata.
        
        Args:
            key: The secret key
            value: The secret value
            ttl: Time to live in seconds
            metadata: Optional metadata dictionary
        """
        encrypted_value = self._cipher.encrypt(value.encode()).decode()
        
        expiry_time = None
        if ttl:
            expiry_time = datetime.now() + timedelta(seconds=ttl)
        
        self._storage[key] = {
            "value": encrypted_value,
            "metadata": metadata or {},
            "created_at": datetime.now(),
            "expiry_time": expiry_time,
            "version": self._storage.get(key, {}).get("version", 0) + 1
        }
        
        # Log the action
        self._log_action(key, "store", {"ttl": ttl, "has_metadata": metadata is not None})
    
    def retrieve(self, key: str, include_metadata: bool = False) -> Any:
        """
        Retrieve a secret by key.
        
        Args:
            key: The secret key
            include_metadata: Whether to include metadata in response
            
        Returns:
            The decrypted secret value or dict with value and metadata
            
        Raises:
            SecretNotFoundError: If the secret doesn't exist
            SecretExpiredError: If the secret has expired
        """
        if key not in self._storage:
            raise SecretNotFoundError(key)
        
        secret = self._storage[key]
        
        # Check expiration
        if secret["expiry_time"] and datetime.now() > secret["expiry_time"]:
            raise SecretExpiredError(key)
        
        # Decrypt the value
        decrypted_value = self._cipher.decrypt(secret["value"].encode()).decode()
        
        # Log the action
        self._log_action(key, "retrieve")
        
        if include_metadata:
            return {
                "value": decrypted_value,
                "metadata": secret["metadata"]
            }
        
        return decrypted_value
    
    def delete(self, key: str) -> None:
        """
        Delete a secret.
        
        Args:
            key: The secret key
            
        Raises:
            SecretNotFoundError: If the secret doesn't exist
        """
        if key not in self._storage:
            raise SecretNotFoundError(key)
        
        del self._storage[key]
        self._log_action(key, "delete")
    
    def list_keys(self) -> List[str]:
        """Return a list of all secret keys."""
        return list(self._storage.keys())
    
    def clear(self) -> None:
        """Clear all secrets."""
        self._storage.clear()
        self._audit_log.clear()
    
    def get_audit_log(self, key: str) -> List[Dict[str, Any]]:
        """
        Get the audit log for a specific secret.
        
        Args:
            key: The secret key
            
        Returns:
            List of audit log entries
        """
        return self._audit_log.get(key, [])
    
    def rotate(self, key: str, new_value: str) -> None:
        """
        Rotate a secret to a new value.
        
        Args:
            key: The secret key
            new_value: The new secret value
            
        Raises:
            SecretNotFoundError: If the secret doesn't exist
        """
        if key not in self._storage:
            raise SecretNotFoundError(key)
        
        # Store old metadata and TTL info
        old_secret = self._storage[key]
        metadata = old_secret.get("metadata")
        
        # Store as new version
        self.store(key, new_value, metadata=metadata)
        self._log_action(key, "rotate")
    
    def get_secret_history(self, key: str) -> List[Dict[str, Any]]:
        """
        Get the history of a secret (versions).
        
        Args:
            key: The secret key
            
        Returns:
            List of secret versions
        """
        if key not in self._storage:
            raise SecretNotFoundError(key)
        
        # Return audit log entries showing updates
        history = [entry for entry in self._audit_log.get(key, []) if entry["action"] in ["store", "rotate"]]
        return history
    
    def _log_action(self, key: str, action: str, details: Optional[Dict[str, Any]] = None) -> None:
        """
        Log an action on a secret.
        
        Args:
            key: The secret key
            action: The action performed
            details: Optional details about the action
        """
        if key not in self._audit_log:
            self._audit_log[key] = []
        
        log_entry = {
            "action": action,
            "timestamp": datetime.now().isoformat(),
            "details": details or {}
        }
        
        self._audit_log[key].append(log_entry)
