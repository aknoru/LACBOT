#!/usr/bin/env python3
"""
LACBOT Setup Script - Automated installation and configuration
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
            'node': {'command': 'node --version', 'min_version': '16'},
            'npm': {'command': 'npm --version', 'min_version': '8'},
            'git': {'command': 'git --version', 'min_version': '2.0'}
        }
        
        missing = []
        for tool, config in requirements.items():
            try:
                result = subprocess.run(config['command'], shell=True, capture_output=True, text=True)
                if result.returncode == 0:
                    print(f"✅ {tool}: {result.stdout.strip()}")
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
        print("📁 Creating project directories...")
        
        directories = [
            "backend/app/api/routes",
            "backend/app/core",
            "backend/app/models",
            "backend/app/services",
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
            print(f"✅ Created: {directory}")
    
    def create_env_file(self):
        """Create environment configuration file"""
        print("⚙️ Creating environment configuration...")
        
        env_file = self.project_root / ".env"
        
        if env_file.exists():
            print("⚠️ .env file already exists. Skipping creation.")
            return
        
        # Generate secret key
        secret_key = self.generate_secret_key()
        
        env_content = f"""# LACBOT Environment Configuration
# Generated on {subprocess.run(['date'], capture_output=True, text=True).stdout.strip()}

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
"""
        
        with open(env_file, 'w') as f:
            f.write(env_content)
        
        print("✅ Created .env file")
        print("⚠️ Please update the .env file with your actual API keys and configuration")
    
    def install_backend_dependencies(self):
        """Install Python dependencies"""
        print("🐍 Installing Python dependencies...")
        
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
            
            print("✅ Backend dependencies installed successfully")
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install backend dependencies: {e}")
            sys.exit(1)
        
        os.chdir(self.project_root)
    
    def install_frontend_dependencies(self):
        """Install Node.js dependencies"""
        print("📦 Installing frontend dependencies...")
        
        # Create package.json if it doesn't exist
        package_json = self.frontend_dir / "package.json"
        if not package_json.exists():
            package_content = {
                "name": "lacbot-frontend",
                "version": "1.0.0",
                "private": True,
                "dependencies": {
                    "react": "^18.2.0",
                    "react-dom": "^18.2.0",
                    "lucide-react": "^0.294.0",
                    "axios": "^1.6.0"
                },
                "scripts": {
                    "start": "react-scripts start",
                    "build": "react-scripts build",
                    "test": "react-scripts test",
                    "eject": "react-scripts eject"
                },
                "eslintConfig": {
                    "extends": ["react-app", "react-app/jest"]
                },
                "browserslist": {
                    "production": [">0.2%", "not dead", "not op_mini all"],
                    "development": ["last 1 chrome version", "last 1 firefox version", "last 1 safari version"]
                },
                "devDependencies": {
                    "react-scripts": "5.0.1"
                }
            }
            
            with open(package_json, 'w') as f:
                json.dump(package_content, f, indent=2)
        
        os.chdir(self.frontend_dir)
        
        try:
            subprocess.run(["npm", "install"], check=True)
            print("✅ Frontend dependencies installed successfully")
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install frontend dependencies: {e}")
            sys.exit(1)
        
        os.chdir(self.project_root)
    
    def install_dashboard_dependencies(self):
        """Install dashboard dependencies"""
        print("📊 Installing dashboard dependencies...")
        
        dashboard_requirements = [
            "streamlit==1.29.0",
            "plotly==5.17.0",
            "pandas==2.1.4",
            "requests==2.31.0"
        ]
        
        os.chdir(self.dashboards_dir)
        
        try:
            # Create virtual environment for dashboards
            subprocess.run([sys.executable, "-m", "venv", "venv"], check=True)
            
            if os.name == 'nt':  # Windows
                pip_cmd = str(self.dashboards_dir / "venv" / "Scripts" / "pip")
            else:  # Unix/Linux/macOS
                pip_cmd = str(self.dashboards_dir / "venv" / "bin" / "pip")
            
            subprocess.run([pip_cmd, "install", "--upgrade", "pip"], check=True)
            
            for req in dashboard_requirements:
                subprocess.run([pip_cmd, "install", req], check=True)
            
            print("✅ Dashboard dependencies installed successfully")
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install dashboard dependencies: {e}")
            sys.exit(1)
        
        os.chdir(self.project_root)
    
    def create_startup_scripts(self):
        """Create startup scripts for different environments"""
        print("🚀 Creating startup scripts...")
        
        # Windows batch script
        windows_script = """@echo off
echo Starting LACBOT Development Environment...

echo Starting Backend API...
cd backend
call venv\\Scripts\\activate
start "LACBOT Backend" cmd /k "uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"

echo Starting Frontend...
cd ..\\frontend
start "LACBOT Frontend" cmd /k "npm start"

echo Starting Super User Dashboard...
cd ..\\dashboards
call venv\\Scripts\\activate
start "LACBOT Super Dashboard" cmd /k "streamlit run super_user_dashboard.py --server.port 8501"

echo Starting Volunteer Dashboard...
start "LACBOT Volunteer Dashboard" cmd /k "streamlit run volunteer_dashboard.py --server.port 8502"

echo All services starting...
echo Backend: http://localhost:8000
echo Frontend: http://localhost:3000
echo Super Dashboard: http://localhost:8501
echo Volunteer Dashboard: http://localhost:8502
pause
"""
        
        with open(self.project_root / "start_dev.bat", 'w') as f:
            f.write(windows_script)
        
        # Unix/Linux/macOS shell script
        unix_script = """#!/bin/bash
echo "Starting LACBOT Development Environment..."

# Function to start service in background
start_service() {
    local name=$1
    local cmd=$2
    local port=$3
    
    echo "Starting $name on port $port..."
    $cmd &
    echo $! > "${name}_pid.txt"
}

# Start Backend API
cd backend
source venv/bin/activate
start_service "backend" "uvicorn app.main:app --reload --host 0.0.0.0 --port 8000" "8000"
cd ..

# Start Frontend
cd frontend
start_service "frontend" "npm start" "3000"
cd ..

# Start Super User Dashboard
cd dashboards
source venv/bin/activate
start_service "super_dashboard" "streamlit run super_user_dashboard.py --server.port 8501" "8501"
start_service "volunteer_dashboard" "streamlit run volunteer_dashboard.py --server.port 8502" "8502"
cd ..

echo "All services starting..."
echo "Backend: http://localhost:8000"
echo "Frontend: http://localhost:3000"
echo "Super Dashboard: http://localhost:8501"
echo "Volunteer Dashboard: http://localhost:8502"

# Function to cleanup on exit
cleanup() {
    echo "Stopping all services..."
    for pid_file in *_pid.txt; do
        if [ -f "$pid_file" ]; then
            kill $(cat "$pid_file") 2>/dev/null
            rm "$pid_file"
        fi
    done
}

trap cleanup EXIT

echo "Press Ctrl+C to stop all services"
wait
"""
        
        unix_script_path = self.project_root / "start_dev.sh"
        with open(unix_script_path, 'w') as f:
            f.write(unix_script)
        
        # Make script executable on Unix systems
        if os.name != 'nt':
            os.chmod(unix_script_path, 0o755)
        
        print("✅ Startup scripts created")
    
    def create_documentation(self):
        """Create basic documentation"""
        print("📚 Creating documentation...")
        
        docs_dir = self.project_root / "docs"
        docs_dir.mkdir(exist_ok=True)
        
        # Quick Start Guide
        quick_start = """# LACBOT Quick Start Guide

## Prerequisites
- Python 3.9+
- Node.js 16+
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
python setup.py
```

3. Configure environment variables in `.env` file

4. Start development environment:
```bash
# Windows
start_dev.bat

# Unix/Linux/macOS
./start_dev.sh
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
        
        print("✅ Documentation created")
    
    def run_setup(self):
        """Run the complete setup process"""
        print("LACBOT Setup - Campus Multilingual Chatbot")
        print("=" * 50)
        
        try:
            self.check_requirements()
            self.create_directories()
            self.create_env_file()
            self.install_backend_dependencies()
            self.install_frontend_dependencies()
            self.install_dashboard_dependencies()
            self.create_startup_scripts()
            self.create_documentation()
            
            print("\nSetup completed successfully!")
            print("\nNext steps:")
            print("1. Update the .env file with your API keys")
            print("2. Set up your Supabase database")
            print("3. Configure Twilio for WhatsApp integration")
            print("4. Run 'python start_dev.py' to start development")
            print("\nFor detailed instructions, see docs/QUICKSTART.md")
            
        except KeyboardInterrupt:
            print("\n❌ Setup interrupted by user")
            sys.exit(1)
        except Exception as e:
            print(f"\n❌ Setup failed: {e}")
            sys.exit(1)

if __name__ == "__main__":
    setup = LACBOTSetup()
    setup.run_setup()
