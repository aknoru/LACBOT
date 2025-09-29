#!/usr/bin/env python3
"""
Simple LACBOT Setup Script - Windows Compatible
"""

import os
import sys
import subprocess
import json
import shutil
from pathlib import Path
import secrets
import string

class LACBOTSetup:
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.backend_dir = self.project_root / "backend"
        self.frontend_dir = self.project_root / "frontend"
        self.dashboards_dir = self.project_root / "dashboards"
        
    def generate_secret_key(self, length=32):
        """Generate a secure secret key"""
        alphabet = string.ascii_letters + string.digits
        return ''.join(secrets.choice(alphabet) for _ in range(length))
    
    def check_requirements(self):
        """Check if required software is installed"""
        print("Checking system requirements...")
        
        requirements = {
            'python': {'command': 'python --version', 'min_version': '3.9'},
            'git': {'command': 'git --version', 'min_version': '2.0'}
        }
        
        missing = []
        for tool, config in requirements.items():
            try:
                result = subprocess.run(config['command'], shell=True, capture_output=True, text=True)
                if result.returncode == 0:
                    print(f"OK {tool}: {result.stdout.strip()}")
                else:
                    missing.append(tool)
            except FileNotFoundError:
                missing.append(tool)
        
        if missing:
            print(f"Missing required software: {', '.join(missing)}")
            print("\nPlease install the missing software and run this script again.")
            sys.exit(1)
        
        print("All requirements satisfied!")
    
    def create_directories(self):
        """Create necessary directories"""
        print("Creating project directories...")
        
        directories = [
            "backend/app/api/routes",
            "backend/app/core",
            "backend/app/models",
            "backend/app/services",
            "backend/app/middleware",
            "frontend/src/components",
            "frontend/public",
            "dashboards",
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
        print("Creating environment configuration...")
        
        env_file = self.project_root / ".env"
        
        if env_file.exists():
            print(".env file already exists. Skipping creation.")
            return
        
        # Generate secret key
        secret_key = self.generate_secret_key()
        
        env_content = f"""# LACBOT Environment Configuration

# Database Configuration
SUPABASE_URL=your_supabase_project_url
SUPABASE_KEY=your_supabase_anon_key
SUPABASE_SERVICE_KEY=your_supabase_service_key

# Security
SECRET_KEY={secret_key}
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# AI Model Configuration
HUGGINGFACE_API_TOKEN=your_huggingface_token
OPENAI_API_KEY=your_openai_api_key

# WhatsApp Integration
TWILIO_ACCOUNT_SID=your_twilio_account_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token
TWILIO_WHATSAPP_NUMBER=whatsapp:+14155238886

# Application Settings
DEBUG=True
HOST=0.0.0.0
PORT=8000
FRONTEND_URL=http://localhost:3000

# Language Models
DEFAULT_LANGUAGE=en
SUPPORTED_LANGUAGES=en,hi,ta,te,bn,mr,gu

# Notification Settings
ENABLE_NOTIFICATIONS=True
NOTIFICATION_INTERVAL=24

# File Upload Settings
MAX_FILE_SIZE=10485760
ALLOWED_EXTENSIONS=pdf,txt,docx

# Rate Limiting
RATE_LIMIT_PER_MINUTE=60
RATE_LIMIT_BURST=100

# Security Configuration
ENCRYPTION_ENABLED=True
AUDIT_LOGGING=True
RATE_LIMITING=True
CSRF_PROTECTION=True
SECURITY_HEADERS=True
INPUT_VALIDATION=True
"""
        
        with open(env_file, 'w') as f:
            f.write(env_content)
        
        print("Created .env file")
        print("Please update the .env file with your actual API keys and configuration")
    
    def install_backend_dependencies(self):
        """Install Python dependencies"""
        print("Installing Python dependencies...")
        
        os.chdir(self.backend_dir)
        
        try:
            # Create virtual environment
            subprocess.run([sys.executable, "-m", "venv", "venv"], check=True)
            
            # Activate virtual environment and install dependencies
            if os.name == 'nt':  # Windows
                pip_cmd = str(self.backend_dir / "venv" / "Scripts" / "pip")
                python_cmd = str(self.backend_dir / "venv" / "Scripts" / "python")
            else:  # Unix/Linux/macOS
                pip_cmd = str(self.backend_dir / "venv" / "bin" / "pip")
                python_cmd = str(self.backend_dir / "venv" / "bin" / "python")
            
            subprocess.run([pip_cmd, "install", "--upgrade", "pip"], check=True)
            subprocess.run([pip_cmd, "install", "-r", "requirements.txt"], check=True)
            
            print("Backend dependencies installed successfully")
            
        except subprocess.CalledProcessError as e:
            print(f"Failed to install backend dependencies: {e}")
            sys.exit(1)
        
        os.chdir(self.project_root)
    
    def create_documentation(self):
        """Create basic documentation"""
        print("Creating documentation...")
        
        docs_dir = self.project_root / "docs"
        docs_dir.mkdir(exist_ok=True)
        
        # Quick Start Guide
        quick_start = """# LACBOT Quick Start Guide

## Prerequisites
- Python 3.9+
- Git
- Supabase account
- Twilio account (for WhatsApp)

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd LACBOT
```

2. Run the setup script:
```bash
python setup_simple.py
```

3. Configure environment variables in `.env` file

4. Start development environment:
```bash
python start_dev.py
```

## Access Points

- **Backend API**: http://localhost:8000
- **Frontend Widget**: http://localhost:3000
- **Super User Dashboard**: http://localhost:8501
- **Volunteer Dashboard**: http://localhost:8502

## First Steps

1. Create a superuser account
2. Add FAQ content
3. Configure WhatsApp integration
4. Test the chatbot

## Support

For issues and questions, please refer to the full documentation or contact the development team.
"""
        
        with open(docs_dir / "QUICKSTART.md", 'w') as f:
            f.write(quick_start)
        
        print("Documentation created")
    
    def run_setup(self):
        """Run the complete setup process"""
        print("LACBOT Setup - Campus Multilingual Chatbot")
        print("=" * 50)
        
        try:
            self.check_requirements()
            self.create_directories()
            self.create_env_file()
            self.install_backend_dependencies()
            self.create_documentation()
            
            print("\nSetup completed successfully!")
            print("\nNext steps:")
            print("1. Update the .env file with your API keys")
            print("2. Set up your Supabase database")
            print("3. Configure Twilio for WhatsApp integration")
            print("4. Run 'python start_dev.py' to start development")
            print("\nFor detailed instructions, see docs/QUICKSTART.md")
            
        except KeyboardInterrupt:
            print("\nSetup interrupted by user")
            sys.exit(1)
        except Exception as e:
            print(f"\nSetup failed: {e}")
            sys.exit(1)

if __name__ == "__main__":
    setup = LACBOTSetup()
    setup.run_setup()
