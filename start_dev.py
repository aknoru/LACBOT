#!/usr/bin/env python3
"""
Development startup script for LACBOT
"""

import subprocess
import sys
import os
import time
import signal
from pathlib import Path

class LACBOTDevStarter:
    def __init__(self):
        self.processes = []
        self.project_root = Path(__file__).parent
        
    def start_backend(self):
        """Start the backend API server"""
        print("🚀 Starting Backend API...")
        
        backend_dir = self.project_root / "backend"
        os.chdir(backend_dir)
        
        if os.name == 'nt':  # Windows
            python_cmd = str(backend_dir / "venv" / "Scripts" / "python")
        else:  # Unix/Linux/macOS
            python_cmd = str(backend_dir / "venv" / "bin" / "python")
        
        try:
            process = subprocess.Popen([
                python_cmd, "-m", "uvicorn", 
                "app.main:app", 
                "--reload", 
                "--host", "0.0.0.0", 
                "--port", "8000"
            ])
            self.processes.append(("Backend API", process))
            print("✅ Backend API started on http://localhost:8000")
            return True
        except Exception as e:
            print(f"❌ Failed to start Backend API: {e}")
            return False
    
    def start_frontend(self):
        """Start the frontend React app"""
        print("🎨 Starting Frontend...")
        
        frontend_dir = self.project_root / "frontend"
        os.chdir(frontend_dir)
        
        try:
            process = subprocess.Popen(["npm", "start"])
            self.processes.append(("Frontend", process))
            print("✅ Frontend started on http://localhost:3000")
            return True
        except Exception as e:
            print(f"❌ Failed to start Frontend: {e}")
            return False
    
    def start_super_dashboard(self):
        """Start the super user dashboard"""
        print("👑 Starting Super User Dashboard...")
        
        dashboards_dir = self.project_root / "dashboards"
        os.chdir(dashboards_dir)
        
        if os.name == 'nt':  # Windows
            python_cmd = str(dashboards_dir / "venv" / "Scripts" / "python")
        else:  # Unix/Linux/macOS
            python_cmd = str(dashboards_dir / "venv" / "bin" / "python")
        
        try:
            process = subprocess.Popen([
                python_cmd, "-m", "streamlit", "run",
                "super_user_dashboard.py",
                "--server.port", "8501",
                "--server.address", "0.0.0.0"
            ])
            self.processes.append(("Super Dashboard", process))
            print("✅ Super User Dashboard started on http://localhost:8501")
            return True
        except Exception as e:
            print(f"❌ Failed to start Super Dashboard: {e}")
            return False
    
    def start_volunteer_dashboard(self):
        """Start the volunteer dashboard"""
        print("👥 Starting Volunteer Dashboard...")
        
        dashboards_dir = self.project_root / "dashboards"
        os.chdir(dashboards_dir)
        
        if os.name == 'nt':  # Windows
            python_cmd = str(dashboards_dir / "venv" / "Scripts" / "python")
        else:  # Unix/Linux/macOS
            python_cmd = str(dashboards_dir / "venv" / "bin" / "python")
        
        try:
            process = subprocess.Popen([
                python_cmd, "-m", "streamlit", "run",
                "volunteer_dashboard.py",
                "--server.port", "8502",
                "--server.address", "0.0.0.0"
            ])
            self.processes.append(("Volunteer Dashboard", process))
            print("✅ Volunteer Dashboard started on http://localhost:8502")
            return True
        except Exception as e:
            print(f"❌ Failed to start Volunteer Dashboard: {e}")
            return False
    
    def cleanup(self):
        """Clean up all processes"""
        print("\n🛑 Shutting down all services...")
        
        for name, process in self.processes:
            try:
                print(f"Stopping {name}...")
                process.terminate()
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                print(f"Force killing {name}...")
                process.kill()
            except Exception as e:
                print(f"Error stopping {name}: {e}")
        
        print("✅ All services stopped")
    
    def signal_handler(self, signum, frame):
        """Handle interrupt signals"""
        print(f"\nReceived signal {signum}")
        self.cleanup()
        sys.exit(0)
    
    def check_dependencies(self):
        """Check if all dependencies are installed"""
        print("🔍 Checking dependencies...")
        
        # Check backend
        backend_dir = self.project_root / "backend"
        if os.name == 'nt':
            venv_path = backend_dir / "venv" / "Scripts" / "python"
        else:
            venv_path = backend_dir / "venv" / "bin" / "python"
        
        if not venv_path.exists():
            print("❌ Backend virtual environment not found. Run 'python setup.py' first.")
            return False
        
        # Check frontend
        frontend_dir = self.project_root / "frontend"
        node_modules = frontend_dir / "node_modules"
        if not node_modules.exists():
            print("❌ Frontend dependencies not found. Run 'python setup.py' first.")
            return False
        
        # Check dashboards
        dashboards_dir = self.project_root / "dashboards"
        if os.name == 'nt':
            venv_path = dashboards_dir / "venv" / "Scripts" / "python"
        else:
            venv_path = dashboards_dir / "venv" / "bin" / "python"
        
        if not venv_path.exists():
            print("❌ Dashboard virtual environment not found. Run 'python setup.py' first.")
            return False
        
        print("✅ All dependencies found")
        return True
    
    def run(self):
        """Main function to start all services"""
        print("🎓 LACBOT Development Environment")
        print("=" * 50)
        
        # Check dependencies
        if not self.check_dependencies():
            sys.exit(1)
        
        # Set up signal handlers
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        try:
            # Start all services
            services_started = 0
            total_services = 4
            
            if self.start_backend():
                services_started += 1
                time.sleep(2)  # Give backend time to start
            
            if self.start_frontend():
                services_started += 1
                time.sleep(2)  # Give frontend time to start
            
            if self.start_super_dashboard():
                services_started += 1
                time.sleep(2)  # Give dashboard time to start
            
            if self.start_volunteer_dashboard():
                services_started += 1
            
            if services_started < total_services:
                print(f"⚠️ Only {services_started}/{total_services} services started successfully")
            else:
                print("\n🎉 All services started successfully!")
            
            # Display access information
            print("\n" + "=" * 50)
            print("📱 Access Points:")
            print("  Backend API:      http://localhost:8000")
            print("  API Documentation: http://localhost:8000/docs")
            print("  Frontend:         http://localhost:3000")
            print("  Super Dashboard:  http://localhost:8501")
            print("  Volunteer Dashboard: http://localhost:8502")
            print("=" * 50)
            
            print("\n💡 Tips:")
            print("  - Press Ctrl+C to stop all services")
            print("  - Check the logs above for any errors")
            print("  - Make sure your .env file is configured")
            print("  - Load sample data with: python scripts/load_sample_data.py")
            
            # Wait for user to stop
            print("\n⏳ Services are running... Press Ctrl+C to stop")
            
            while True:
                time.sleep(1)
                
                # Check if any process has died
                for name, process in self.processes[:]:
                    if process.poll() is not None:
                        print(f"❌ {name} has stopped unexpectedly")
                        self.processes.remove((name, process))
                
                if not self.processes:
                    print("❌ All services have stopped")
                    break
                    
        except KeyboardInterrupt:
            print("\n👋 Shutdown requested by user")
        except Exception as e:
            print(f"\n❌ Unexpected error: {e}")
        finally:
            self.cleanup()

if __name__ == "__main__":
    starter = LACBOTDevStarter()
    starter.run()
