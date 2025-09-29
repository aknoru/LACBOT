#!/usr/bin/env python3
"""
Quick LACBOT Setup - Essential Components Only
"""

import os
import sys
import subprocess
import json
from pathlib import Path
import secrets
import string

class QuickSetup:
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.backend_dir = self.project_root / "backend"
        
    def generate_secret_key(self, length=32):
        """Generate a secure secret key"""
        alphabet = string.ascii_letters + string.digits
        return ''.join(secrets.choice(alphabet) for _ in range(length))
    
    def check_python(self):
        """Check Python version"""
        print("Checking Python...")
        
        if sys.version_info < (3, 9):
            print(f"Python 3.9+ required, found {sys.version}")
            sys.exit(1)
        
        print(f"OK Python: {sys.version.split()[0]}")
    
    def create_directories(self):
        """Create necessary directories"""
        print("Creating directories...")
        
        directories = [
            "data/chroma_db",
            "data/documents", 
            "logs",
            "ssl"
        ]
        
        for directory in directories:
            dir_path = self.project_root / directory
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"Created: {directory}")
    
    def create_env_file(self):
        """Create environment configuration file"""
        print("Creating .env file...")
        
        env_file = self.project_root / ".env"
        
        if env_file.exists():
            print(".env file already exists.")
            return
        
        secret_key = self.generate_secret_key()
        
        env_content = f"""# LACBOT Environment Configuration

# Database Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_supabase_anon_key
SUPABASE_SERVICE_KEY=your_supabase_service_key

# Security
SECRET_KEY={secret_key}
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# AI Model Configuration
HUGGINGFACE_API_TOKEN=your_huggingface_token

# Application Settings
DEBUG=True
HOST=0.0.0.0
PORT=8000
FRONTEND_URL=http://localhost:3000

# Language Models
DEFAULT_LANGUAGE=en
SUPPORTED_LANGUAGES=en,hi,ta,te,bn,mr,gu

# Rate Limiting
RATE_LIMIT_PER_MINUTE=60
RATE_LIMIT_BURST=100

# Security Configuration
ENCRYPTION_ENABLED=True
AUDIT_LOGGING=True
RATE_LIMITING=True
"""
        
        with open(env_file, 'w') as f:
            f.write(env_content)
        
        print("Created .env file with generated secret key")
    
    def install_dependencies(self):
        """Install Python dependencies"""
        print("Installing dependencies...")
        
        # Install core dependencies
        packages = [
            "fastapi",
            "uvicorn[standard]",
            "python-multipart",
            "python-jose[cryptography]",
            "passlib[bcrypt]",
            "python-dotenv",
            "supabase",
            "requests",
            "cryptography",
            "pydantic",
            "httpx"
        ]
        
        for package in packages:
            try:
                print(f"Installing {package}...")
                subprocess.run([sys.executable, "-m", "pip", "install", package], 
                             check=True, capture_output=True)
            except subprocess.CalledProcessError as e:
                print(f"Failed to install {package}: {e}")
                # Continue with other packages
    
    def create_sample_data(self):
        """Create sample data files"""
        print("Creating sample data...")
        
        # Create sample FAQs
        sample_faqs = {
            "faqs": [
                {
                    "question": "When is the deadline for semester fee payment?",
                    "answer": "The deadline for semester fee payment is March 15, 2024. You can pay online through the student portal.",
                    "category": "fees",
                    "language": "en",
                    "priority": 5
                },
                {
                    "question": "How can I apply for scholarships?",
                    "answer": "You can apply for scholarships through the online portal. Visit the financial aid section on the college website.",
                    "category": "scholarships", 
                    "language": "en",
                    "priority": 4
                }
            ]
        }
        
        data_dir = self.project_root / "data"
        data_dir.mkdir(exist_ok=True)
        
        with open(data_dir / "sample_faqs.json", 'w') as f:
            json.dump(sample_faqs, f, indent=2)
        
        print("Created sample FAQ data")
    
    def run_setup(self):
        """Run the quick setup"""
        print("LACBOT Quick Setup")
        print("=" * 30)
        
        try:
            self.check_python()
            self.create_directories()
            self.create_env_file()
            self.install_dependencies()
            self.create_sample_data()
            
            print("\nQuick setup completed!")
            print("\nNext steps:")
            print("1. Update .env file with your API keys")
            print("2. Run: python backend/app/main.py")
            print("3. Access: http://localhost:8000/docs")
            
        except Exception as e:
            print(f"\nSetup failed: {e}")
            sys.exit(1)

if __name__ == "__main__":
    setup = QuickSetup()
    setup.run_setup()
