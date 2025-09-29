"""
Advanced encryption and data protection utilities for LACBOT
"""

import os
import base64
import hashlib
import secrets
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
from typing import Optional, Dict, Any
import json
import logging

logger = logging.getLogger(__name__)

class EncryptionManager:
    """Advanced encryption manager for data protection"""
    
    def __init__(self):
        self.backend = default_backend()
        self._symmetric_key = None
        self._public_key = None
        self._private_key = None
        self._initialize_keys()
    
    def _initialize_keys(self):
        """Initialize encryption keys"""
        try:
            # Generate or load symmetric key
            self._symmetric_key = self._get_or_generate_symmetric_key()
            
            # Generate or load asymmetric keys
            self._public_key, self._private_key = self._get_or_generate_asymmetric_keys()
            
            logger.info("✅ Encryption keys initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize encryption keys: {e}")
            raise
    
    def _get_or_generate_symmetric_key(self) -> bytes:
        """Get or generate symmetric encryption key"""
        key_file = os.getenv('SYMMETRIC_KEY_FILE', './data/.symmetric_key')
        
        if os.path.exists(key_file):
            with open(key_file, 'rb') as f:
                return f.read()
        else:
            # Generate new key
            key = Fernet.generate_key()
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(key_file), exist_ok=True)
            
            # Save key with restricted permissions
            with open(key_file, 'wb') as f:
                f.write(key)
            os.chmod(key_file, 0o600)  # Only owner can read/write
            
            return key
    
    def _get_or_generate_asymmetric_keys(self) -> tuple:
        """Get or generate asymmetric encryption keys"""
        private_key_file = os.getenv('PRIVATE_KEY_FILE', './data/.private_key')
        public_key_file = os.getenv('PUBLIC_KEY_FILE', './data/.public_key')
        
        if os.path.exists(private_key_file) and os.path.exists(public_key_file):
            # Load existing keys
            with open(private_key_file, 'rb') as f:
                private_key = serialization.load_pem_private_key(
                    f.read(), password=None, backend=self.backend
                )
            
            with open(public_key_file, 'rb') as f:
                public_key = serialization.load_pem_public_key(
                    f.read(), backend=self.backend
                )
        else:
            # Generate new keys
            private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=2048,
                backend=self.backend
            )
            public_key = private_key.public_key()
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(private_key_file), exist_ok=True)
            
            # Save private key
            with open(private_key_file, 'wb') as f:
                f.write(private_key.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.PKCS8,
                    encryption_algorithm=serialization.NoEncryption()
                ))
            os.chmod(private_key_file, 0o600)
            
            # Save public key
            with open(public_key_file, 'wb') as f:
                f.write(public_key.public_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PublicFormat.SubjectPublicKeyInfo
                ))
            os.chmod(public_key_file, 0o644)
        
        return public_key, private_key
    
    def encrypt_sensitive_data(self, data: str) -> str:
        """Encrypt sensitive data using symmetric encryption"""
        try:
            fernet = Fernet(self._symmetric_key)
            encrypted_data = fernet.encrypt(data.encode('utf-8'))
            return base64.b64encode(encrypted_data).decode('utf-8')
        except Exception as e:
            logger.error(f"❌ Failed to encrypt data: {e}")
            raise
    
    def decrypt_sensitive_data(self, encrypted_data: str) -> str:
        """Decrypt sensitive data using symmetric encryption"""
        try:
            fernet = Fernet(self._symmetric_key)
            decoded_data = base64.b64decode(encrypted_data.encode('utf-8'))
            decrypted_data = fernet.decrypt(decoded_data)
            return decrypted_data.decode('utf-8')
        except Exception as e:
            logger.error(f"❌ Failed to decrypt data: {e}")
            raise
    
    def encrypt_message(self, message: str) -> Dict[str, Any]:
        """Encrypt message with additional metadata"""
        try:
            # Generate unique message ID
            message_id = secrets.token_hex(16)
            
            # Encrypt the message
            encrypted_content = self.encrypt_sensitive_data(message)
            
            # Create hash for integrity verification
            content_hash = hashlib.sha256(message.encode('utf-8')).hexdigest()
            
            return {
                'message_id': message_id,
                'encrypted_content': encrypted_content,
                'content_hash': content_hash,
                'encryption_method': 'AES-256-GCM',
                'timestamp': self._get_timestamp()
            }
        except Exception as e:
            logger.error(f"❌ Failed to encrypt message: {e}")
            raise
    
    def decrypt_message(self, encrypted_message: Dict[str, Any]) -> str:
        """Decrypt message with integrity verification"""
        try:
            # Decrypt the content
            decrypted_content = self.decrypt_sensitive_data(
                encrypted_message['encrypted_content']
            )
            
            # Verify integrity
            content_hash = hashlib.sha256(decrypted_content.encode('utf-8')).hexdigest()
            if content_hash != encrypted_message['content_hash']:
                raise ValueError("Message integrity check failed")
            
            return decrypted_content
        except Exception as e:
            logger.error(f"❌ Failed to decrypt message: {e}")
            raise
    
    def hash_password(self, password: str, salt: Optional[bytes] = None) -> Dict[str, str]:
        """Generate secure password hash using PBKDF2"""
        try:
            if salt is None:
                salt = os.urandom(32)
            
            # Use PBKDF2 with SHA-256
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
                backend=self.backend
            )
            
            key = base64.urlsafe_b64encode(kdf.derive(password.encode('utf-8')))
            
            return {
                'hash': key.decode('utf-8'),
                'salt': base64.urlsafe_b64encode(salt).decode('utf-8')
            }
        except Exception as e:
            logger.error(f"❌ Failed to hash password: {e}")
            raise
    
    def verify_password(self, password: str, password_hash: str, salt: str) -> bool:
        """Verify password against hash"""
        try:
            salt_bytes = base64.urlsafe_b64decode(salt.encode('utf-8'))
            new_hash = self.hash_password(password, salt_bytes)
            return new_hash['hash'] == password_hash
        except Exception as e:
            logger.error(f"❌ Failed to verify password: {e}")
            return False
    
    def generate_api_key(self) -> str:
        """Generate secure API key"""
        return secrets.token_urlsafe(32)
    
    def generate_session_token(self) -> str:
        """Generate secure session token"""
        return secrets.token_urlsafe(48)
    
    def encrypt_database_field(self, field_value: str) -> str:
        """Encrypt database field value"""
        return self.encrypt_sensitive_data(field_value)
    
    def decrypt_database_field(self, encrypted_value: str) -> str:
        """Decrypt database field value"""
        return self.decrypt_sensitive_data(encrypted_value)
    
    def create_audit_hash(self, data: Dict[str, Any]) -> str:
        """Create audit hash for data integrity"""
        try:
            # Sort data to ensure consistent hashing
            sorted_data = json.dumps(data, sort_keys=True)
            return hashlib.sha256(sorted_data.encode('utf-8')).hexdigest()
        except Exception as e:
            logger.error(f"❌ Failed to create audit hash: {e}")
            raise
    
    def _get_timestamp(self) -> str:
        """Get current timestamp in ISO format"""
        from datetime import datetime
        return datetime.utcnow().isoformat()
    
    def get_public_key_pem(self) -> str:
        """Get public key in PEM format"""
        try:
            pem = self._public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            )
            return pem.decode('utf-8')
        except Exception as e:
            logger.error(f"❌ Failed to get public key: {e}")
            raise

# Global encryption manager instance
encryption_manager = EncryptionManager()
