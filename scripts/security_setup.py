#!/usr/bin/env python3
"""
Security setup script for LACBOT
"""

import os
import sys
import subprocess
import secrets
import string
from pathlib import Path
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend

class SecuritySetup:
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.data_dir = self.project_root / "data"
        self.security_dir = self.data_dir / "security"
        
    def generate_secure_secret_key(self, length=64):
        """Generate a cryptographically secure secret key"""
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
        return ''.join(secrets.choice(alphabet) for _ in range(length))
    
    def generate_encryption_keys(self):
        """Generate encryption keys for the application"""
        print("🔐 Generating encryption keys...")
        
        # Ensure security directory exists
        self.security_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate symmetric key
        symmetric_key_path = self.security_dir / ".symmetric_key"
        if not symmetric_key_path.exists():
            symmetric_key = Fernet.generate_key()
            with open(symmetric_key_path, 'wb') as f:
                f.write(symmetric_key)
            os.chmod(symmetric_key_path, 0o600)  # Only owner can read/write
            print(f"✅ Generated symmetric key: {symmetric_key_path}")
        
        # Generate asymmetric key pair
        private_key_path = self.security_dir / ".private_key"
        public_key_path = self.security_dir / ".public_key"
        
        if not private_key_path.exists() or not public_key_path.exists():
            # Generate private key
            private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=2048,
                backend=default_backend()
            )
            
            # Save private key
            with open(private_key_path, 'wb') as f:
                f.write(private_key.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.PKCS8,
                    encryption_algorithm=serialization.NoEncryption()
                ))
            os.chmod(private_key_path, 0o600)
            print(f"✅ Generated private key: {private_key_path}")
            
            # Save public key
            public_key = private_key.public_key()
            with open(public_key_path, 'wb') as f:
                f.write(public_key.public_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PublicFormat.SubjectPublicKeyInfo
                ))
            os.chmod(public_key_path, 0o644)
            print(f"✅ Generated public key: {public_key_path}")
    
    def update_env_file(self):
        """Update .env file with security configurations"""
        print("⚙️ Updating environment configuration...")
        
        env_file = self.project_root / ".env"
        
        if not env_file.exists():
            print("❌ .env file not found. Please run setup.py first.")
            return False
        
        # Generate new secret key if not present
        with open(env_file, 'r') as f:
            content = f.read()
        
        if "SECRET_KEY=your_secret_key_here" in content:
            # Generate a new secret key
            new_secret_key = self.generate_secure_secret_key()
            content = content.replace(
                "SECRET_KEY=your_secret_key_here",
                f"SECRET_KEY={new_secret_key}"
            )
            
            with open(env_file, 'w') as f:
                f.write(content)
            
            print("✅ Updated SECRET_KEY in .env file")
        
        # Add security-specific configurations
        security_configs = """
# Security Configuration
ENCRYPTION_ENABLED=True
AUDIT_LOGGING=True
RATE_LIMITING=True
CSRF_PROTECTION=True
SECURITY_HEADERS=True
INPUT_VALIDATION=True

# Key file paths
SYMMETRIC_KEY_FILE=./data/security/.symmetric_key
PRIVATE_KEY_FILE=./data/security/.private_key
PUBLIC_KEY_FILE=./data/security/.public_key

# Security policies
PASSWORD_MIN_LENGTH=8
SESSION_TIMEOUT_MINUTES=30
MAX_LOGIN_ATTEMPTS=5
ACCOUNT_LOCKOUT_MINUTES=15
API_KEY_LENGTH=32

# Monitoring
SECURITY_MONITORING=True
THREAT_DETECTION=True
ANOMALY_DETECTION=True
AUDIT_RETENTION_DAYS=365
"""
        
        # Check if security configs already exist
        if "ENCRYPTION_ENABLED=True" not in content:
            with open(env_file, 'a') as f:
                f.write(security_configs)
            print("✅ Added security configurations to .env file")
        
        return True
    
    def setup_ssl_certificates(self):
        """Set up SSL certificates for HTTPS"""
        print("🔒 Setting up SSL certificates...")
        
        ssl_dir = self.project_root / "ssl"
        ssl_dir.mkdir(exist_ok=True)
        
        cert_file = ssl_dir / "cert.pem"
        key_file = ssl_dir / "key.pem"
        
        if not cert_file.exists() or not key_file.exists():
            print("📝 Generating self-signed SSL certificate for development...")
            print("⚠️  For production, use proper SSL certificates from a CA")
            
            # Generate self-signed certificate
            subprocess.run([
                "openssl", "req", "-x509", "-newkey", "rsa:4096",
                "-keyout", str(key_file),
                "-out", str(cert_file),
                "-days", "365",
                "-nodes",
                "-subj", "/C=US/ST=State/L=City/O=Organization/CN=localhost"
            ], check=True)
            
            print(f"✅ Generated SSL certificate: {cert_file}")
            print(f"✅ Generated SSL private key: {key_file}")
        else:
            print("✅ SSL certificates already exist")
    
    def create_security_directories(self):
        """Create necessary security directories"""
        print("📁 Creating security directories...")
        
        directories = [
            "data/security",
            "data/audit",
            "data/encrypted",
            "logs/security",
            "backup/encrypted"
        ]
        
        for directory in directories:
            dir_path = self.project_root / directory
            dir_path.mkdir(parents=True, exist_ok=True)
            
            # Set restrictive permissions
            if directory.startswith("data/") or directory.startswith("logs/"):
                os.chmod(dir_path, 0o700)  # Only owner can access
            
            print(f"✅ Created: {directory}")
    
    def setup_firewall_rules(self):
        """Set up basic firewall rules (Linux/macOS only)"""
        print("🔥 Setting up firewall rules...")
        
        if os.name == 'nt':  # Windows
            print("⚠️  Firewall setup not implemented for Windows")
            print("   Please configure Windows Firewall manually")
            return
        
        # Basic UFW rules for Ubuntu/Debian
        try:
            subprocess.run(["which", "ufw"], check=True, capture_output=True)
            
            print("📝 Configuring UFW firewall rules...")
            
            # Default policies
            subprocess.run(["sudo", "ufw", "default", "deny", "incoming"], check=True)
            subprocess.run(["sudo", "ufw", "default", "allow", "outgoing"], check=True)
            
            # Allow SSH (be careful not to lock yourself out)
            subprocess.run(["sudo", "ufw", "allow", "ssh"], check=True)
            
            # Allow HTTP and HTTPS
            subprocess.run(["sudo", "ufw", "allow", "80/tcp"], check=True)
            subprocess.run(["sudo", "ufw", "allow", "443/tcp"], check=True)
            
            # Allow application ports
            subprocess.run(["sudo", "ufw", "allow", "8000/tcp"], check=True)  # Backend API
            subprocess.run(["sudo", "ufw", "allow", "3000/tcp"], check=True)  # Frontend
            subprocess.run(["sudo", "ufw", "allow", "8501/tcp"], check=True)  # Super Dashboard
            subprocess.run(["sudo", "ufw", "allow", "8502/tcp"], check=True)  # Volunteer Dashboard
            
            # Enable firewall
            subprocess.run(["sudo", "ufw", "--force", "enable"], check=True)
            
            print("✅ UFW firewall configured successfully")
            
        except subprocess.CalledProcessError:
            print("⚠️  UFW not found. Please configure firewall manually")
        except Exception as e:
            print(f"⚠️  Firewall setup failed: {e}")
    
    def install_security_dependencies(self):
        """Install additional security dependencies"""
        print("📦 Installing security dependencies...")
        
        security_packages = [
            "cryptography>=41.0.0",
            "PyJWT>=2.8.0",
            "passlib[bcrypt]>=1.7.4",
            "python-jose[cryptography]>=3.3.0"
        ]
        
        for package in security_packages:
            try:
                subprocess.run([
                    sys.executable, "-m", "pip", "install", package
                ], check=True, capture_output=True)
                print(f"✅ Installed: {package}")
            except subprocess.CalledProcessError as e:
                print(f"❌ Failed to install {package}: {e}")
    
    def create_security_scripts(self):
        """Create security utility scripts"""
        print("📝 Creating security utility scripts...")
        
        scripts_dir = self.project_root / "scripts"
        scripts_dir.mkdir(exist_ok=True)
        
        # Security audit script
        audit_script = scripts_dir / "security_audit.py"
        if not audit_script.exists():
            audit_content = '''#!/usr/bin/env python3
"""
Security audit script for LACBOT
"""

import os
import sys
from pathlib import Path
from datetime import datetime

def check_file_permissions():
    """Check file permissions for security"""
    print("🔍 Checking file permissions...")
    
    project_root = Path(__file__).parent.parent
    sensitive_files = [
        "data/.env",
        "data/security/.symmetric_key",
        "data/security/.private_key",
        "ssl/key.pem"
    ]
    
    for file_path in sensitive_files:
        full_path = project_root / file_path
        if full_path.exists():
            stat = full_path.stat()
            mode = oct(stat.st_mode)[-3:]
            if mode != "600":
                print(f"⚠️  {file_path} has permissions {mode}, should be 600")
            else:
                print(f"✅ {file_path} has correct permissions")
        else:
            print(f"❌ {file_path} not found")

def check_ssl_certificates():
    """Check SSL certificate validity"""
    print("🔍 Checking SSL certificates...")
    
    project_root = Path(__file__).parent.parent
    cert_file = project_root / "ssl" / "cert.pem"
    
    if cert_file.exists():
        import subprocess
        try:
            result = subprocess.run([
                "openssl", "x509", "-in", str(cert_file), 
                "-text", "-noout", "-dates"
            ], capture_output=True, text=True, check=True)
            
            print("✅ SSL certificate found")
            print(result.stdout)
        except subprocess.CalledProcessError:
            print("❌ Invalid SSL certificate")
    else:
        print("❌ SSL certificate not found")

def main():
    print("🔐 LACBOT Security Audit")
    print("=" * 40)
    print(f"Audit Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    check_file_permissions()
    print()
    check_ssl_certificates()

if __name__ == "__main__":
    main()
'''
            
            with open(audit_script, 'w') as f:
                f.write(audit_content)
            
            # Make executable
            os.chmod(audit_script, 0o755)
            print(f"✅ Created security audit script: {audit_script}")
        
        # Key rotation script
        rotation_script = scripts_dir / "rotate_keys.py"
        if not rotation_script.exists():
            rotation_content = '''#!/usr/bin/env python3
"""
Key rotation script for LACBOT
"""

import os
import sys
from pathlib import Path
from cryptography.fernet import Fernet

def rotate_symmetric_key():
    """Rotate symmetric encryption key"""
    print("🔄 Rotating symmetric key...")
    
    project_root = Path(__file__).parent.parent
    key_file = project_root / "data" / "security" / ".symmetric_key"
    
    if key_file.exists():
        # Generate new key
        new_key = Fernet.generate_key()
        
        # Backup old key
        backup_file = key_file.with_suffix('.backup')
        key_file.rename(backup_file)
        
        # Write new key
        with open(key_file, 'wb') as f:
            f.write(new_key)
        os.chmod(key_file, 0o600)
        
        print(f"✅ Rotated symmetric key")
        print(f"📁 Old key backed up to: {backup_file}")
        print("⚠️  Note: This will require application restart")
    else:
        print("❌ Symmetric key file not found")

def main():
    print("🔄 LACBOT Key Rotation")
    print("=" * 30)
    
    rotate_symmetric_key()

if __name__ == "__main__":
    main()
'''
            
            with open(rotation_script, 'w') as f:
                f.write(rotation_content)
            
            # Make executable
            os.chmod(rotation_script, 0o755)
            print(f"✅ Created key rotation script: {rotation_script}")
    
    def run_security_tests(self):
        """Run basic security tests"""
        print("🧪 Running security tests...")
        
        try:
            # Test encryption
            from cryptography.fernet import Fernet
            key = Fernet.generate_key()
            fernet = Fernet(key)
            
            test_data = "This is a test message for encryption"
            encrypted = fernet.encrypt(test_data.encode())
            decrypted = fernet.decrypt(encrypted).decode()
            
            if test_data == decrypted:
                print("✅ Encryption/decryption test passed")
            else:
                print("❌ Encryption/decryption test failed")
            
            # Test password hashing
            from passlib.context import CryptContext
            pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
            
            password = "test_password_123"
            hashed = pwd_context.hash(password)
            
            if pwd_context.verify(password, hashed):
                print("✅ Password hashing test passed")
            else:
                print("❌ Password hashing test failed")
            
        except ImportError as e:
            print(f"❌ Security test failed - missing dependency: {e}")
        except Exception as e:
            print(f"❌ Security test failed: {e}")
    
    def run_setup(self):
        """Run the complete security setup"""
        print("🔐 LACBOT Security Setup")
        print("=" * 40)
        
        try:
            self.create_security_directories()
            self.generate_encryption_keys()
            self.update_env_file()
            self.setup_ssl_certificates()
            self.install_security_dependencies()
            self.create_security_scripts()
            self.setup_firewall_rules()
            self.run_security_tests()
            
            print("\n🎉 Security setup completed successfully!")
            print("\nNext steps:")
            print("1. Review and update .env file with your API keys")
            print("2. Run 'python scripts/security_audit.py' to verify setup")
            print("3. Start the application with enhanced security")
            print("4. Monitor security logs regularly")
            print("\n⚠️  Important Security Notes:")
            print("- Keep encryption keys secure and backed up")
            print("- Use proper SSL certificates in production")
            print("- Regularly update dependencies for security patches")
            print("- Monitor security logs for suspicious activity")
            print("- Conduct regular security audits")
            
        except Exception as e:
            print(f"\n❌ Security setup failed: {e}")
            sys.exit(1)

if __name__ == "__main__":
    setup = SecuritySetup()
    setup.run_setup()
