from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2
import base64
from app.config import get_settings
import logging

logger = logging.getLogger(__name__)
settings = get_settings()

class EncryptionService:
    """AES-256 encryption service for storing secrets."""
    
    def __init__(self, key: str = None):
        """Initialize with encryption key."""
        if key is None:
            key = settings.encryption_key
        
        # Derive a key from the encryption key string
        self.key = self._derive_key(key)
        self.cipher_suite = Fernet(self.key)
    
    @staticmethod
    def _derive_key(password: str) -> bytes:
        """Derive a Fernet key from a password."""
        # Use PBKDF2 to derive key from password
        salt = b'securevault_salt'  # In production, use proper salt management
        kdf = PBKDF2(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=480000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key
    
    def encrypt(self, plaintext: str) -> str:
        """Encrypt plaintext and return base64-encoded ciphertext."""
        try:
            encrypted = self.cipher_suite.encrypt(plaintext.encode())
            return base64.b64encode(encrypted).decode()
        except Exception as e:
            logger.error(f"Encryption error: {str(e)}")
            raise ValueError("Failed to encrypt secret")
    
    def decrypt(self, ciphertext: str) -> str:
        """Decrypt base64-encoded ciphertext and return plaintext."""
        try:
            encrypted = base64.b64decode(ciphertext.encode())
            decrypted = self.cipher_suite.decrypt(encrypted)
            return decrypted.decode()
        except Exception as e:
            logger.error(f"Decryption error: {str(e)}")
            raise ValueError("Failed to decrypt secret")

# Global encryption service instance
encryption_service = EncryptionService()