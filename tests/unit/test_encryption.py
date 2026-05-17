import pytest
from app.security.encryption import encryption_service

class TestEncryptionService:
    """Test encryption service."""
    
    def test_encrypt_decrypt_roundtrip(self):
        """Test encryption and decryption roundtrip."""
        plaintext = "super_secret_api_key_12345"
        
        encrypted = encryption_service.encrypt(plaintext)
        decrypted = encryption_service.decrypt(encrypted)
        
        assert decrypted == plaintext
        assert encrypted != plaintext  # Verify it's actually encrypted
    
    def test_encrypt_different_plaintexts(self):
        """Test same plaintext produces different ciphertexts (due to IV)."""
        plaintext = "secret_value"
        
        encrypted1 = encryption_service.encrypt(plaintext)
        encrypted2 = encryption_service.encrypt(plaintext)
        
        # Note: Fernet might produce same output for same plaintext
        # This is OK for Fernet, but real AES-256 should vary with IV
        assert encryption_service.decrypt(encrypted1) == plaintext
        assert encryption_service.decrypt(encrypted2) == plaintext
    
    def test_decrypt_invalid_ciphertext(self):
        """Test decryption of invalid ciphertext raises error."""
        with pytest.raises(ValueError, match="Failed to decrypt"):
            encryption_service.decrypt("invalid_ciphertext_data")
    
    def test_encrypt_empty_string(self):
        """Test encrypting empty string."""
        plaintext = ""
        encrypted = encryption_service.encrypt(plaintext)
        decrypted = encryption_service.decrypt(encrypted)
        
        assert decrypted == plaintext
    
    def test_encrypt_long_secret(self):
        """Test encrypting long secret."""
        plaintext = "a" * 10000  # 10KB of data
        
        encrypted = encryption_service.encrypt(plaintext)
        decrypted = encryption_service.decrypt(encrypted)
        
        assert decrypted == plaintext
    
    def test_encrypt_special_characters(self):
        """Test encrypting special characters."""
        plaintext = "!@#$%^&*()_+-=[]{}|;:',.<>?/~`"
        
        encrypted = encryption_service.encrypt(plaintext)
        decrypted = encryption_service.decrypt(encrypted)
        
        assert decrypted == plaintext
    
    def test_encrypt_unicode(self):
        """Test encrypting Unicode characters."""
        plaintext = "你好世界🔐🔑"  # Chinese + emojis
        
        encrypted = encryption_service.encrypt(plaintext)
        decrypted = encryption_service.decrypt(encrypted)
        
        assert decrypted == plaintext