# 📁 LACBOT Project Files Overview

This document provides a comprehensive overview of all files in the LACBOT project, their purposes, and how they work together to create a complete campus multilingual chatbot solution.

## 📋 File Categories

### 📄 Core Documentation Files
| File | Purpose | Description |
|------|---------|-------------|
| `README.md` | Main documentation | Primary project overview and setup instructions |
| `COMPREHENSIVE_GUIDE.md` | Detailed guide | Complete step-by-step setup and integration instructions |
| `QUICK_REFERENCE.md` | Quick reference | Command reference and troubleshooting guide |
| `SETUP_COMPLETE.md` | Setup summary | Success summary and next steps |
| `PROJECT_FILES.md` | File overview | This file - comprehensive file listing |

### 🔧 Configuration Files
| File | Purpose | Description |
|------|---------|-------------|
| `.env.example` | Environment template | Template for environment variables |
| `requirements.txt` | Python dependencies | All required Python packages |
| `docker-compose.yml` | Docker configuration | Multi-service container orchestration |
| `nginx.conf` | Reverse proxy config | Nginx configuration for production |
| `package.json` | Frontend dependencies | React widget dependencies |

### 🚀 Application Entry Points
| File | Purpose | Description |
|------|---------|-------------|
| `main.py` | Main application | Primary FastAPI application entry point |
| `start_dev.py` | Development starter | Development environment startup script |
| `demo.html` | Interactive demo | Browser-based chatbot demo interface |

### 🛠️ Setup and Utility Scripts
| File | Purpose | Description |
|------|---------|-------------|
| `quick_setup.py` | Quick setup | Automated project setup script |
| `security_setup_simple.py` | Security setup | Security configuration and key generation |
| `setup.py` | Full setup | Comprehensive setup script (with Unicode issues) |
| `setup_simple.py` | Simple setup | Windows-compatible setup script |

### 🏗️ Backend Application Files
| Directory/File | Purpose | Description |
|----------------|---------|-------------|
| `backend/app/main.py` | FastAPI app | Main backend application |
| `backend/app/core/config.py` | Configuration | Application configuration settings |
| `backend/app/core/database.py` | Database setup | Database connection and initialization |
| `backend/app/core/security.py` | Security utilities | Basic security functions |
| `backend/app/core/encryption.py` | Encryption | AES-256 and RSA encryption utilities |
| `backend/app/core/security_enhanced.py` | Enhanced security | Advanced security functions and RBAC |
| `backend/app/middleware/security_middleware.py` | Security middleware | Security middleware implementations |
| `backend/app/api/routes/chat.py` | Chat API | Chat and conversation endpoints |
| `backend/app/api/routes/auth.py` | Authentication API | User authentication endpoints |
| `backend/app/api/routes/admin.py` | Admin API | Administrative functions and user management |
| `backend/app/api/routes/webhook.py` | Webhook API | WhatsApp and other webhook integrations |
| `backend/app/api/routes/security.py` | Security API | Security monitoring and audit endpoints |
| `backend/app/models/security_models.py` | Security models | Pydantic models for security data |
| `backend/app/services/rag_service.py` | RAG service | Retrieval-Augmented Generation implementation |

### 🎨 Frontend Files
| Directory/File | Purpose | Description |
|----------------|---------|-------------|
| `frontend/src/components/ChatWidget.jsx` | Chat widget | React component for embeddable chat widget |
| `frontend/src/App.js` | Main app | Main React application component |
| `frontend/src/index.js` | Entry point | React application entry point |
| `frontend/src/index.css` | Styles | Main CSS styles |
| `frontend/public/index.html` | HTML template | Main HTML template |

### 📊 Dashboard Files
| File | Purpose | Description |
|------|---------|-------------|
| `dashboards/super_user_dashboard.py` | Super user interface | Streamlit dashboard for super users |
| `dashboards/volunteer_dashboard.py` | Volunteer interface | Streamlit dashboard for volunteers |
| `dashboards/normal_user_dashboard.py` | User interface | Streamlit dashboard for normal users |

### 📚 Documentation Files
| File | Purpose | Description |
|------|---------|-------------|
| `docs/SECURITY.md` | Security documentation | Comprehensive security guide |
| `docs/DEPLOYMENT.md` | Deployment guide | Production deployment instructions |
| `docs/MAINTENANCE.md` | Maintenance guide | System maintenance and monitoring |
| `docs/QUICKSTART.md` | Quick start guide | Quick start instructions |

### 🔧 Utility Scripts
| File | Purpose | Description |
|------|---------|-------------|
| `scripts/load_sample_data.py` | Data loader | Script to load sample FAQ data |
| `scripts/security_setup.py` | Advanced security | Advanced security configuration script |

### 🐳 Docker Files
| File | Purpose | Description |
|------|---------|-------------|
| `backend/Dockerfile` | Backend container | Docker configuration for backend |
| `frontend/Dockerfile` | Frontend container | Docker configuration for frontend |

### 📁 Data Directories
| Directory | Purpose | Description |
|-----------|---------|-------------|
| `data/chroma_db/` | Vector database | ChromaDB vector storage for RAG |
| `data/documents/` | Document storage | Uploaded documents and files |
| `data/security/` | Security keys | Encryption keys and certificates |
| `data/audit/` | Audit logs | Security audit logs |
| `data/encrypted/` | Encrypted data | Encrypted data storage |
| `logs/` | Application logs | Application and system logs |
| `logs/security/` | Security logs | Security-specific log files |

## 🔄 File Dependencies and Flow

### Application Startup Flow
```
1. main.py (entry point)
   ↓
2. backend/app/core/config.py (load configuration)
   ↓
3. backend/app/core/database.py (connect to Supabase)
   ↓
4. backend/app/core/security.py (initialize security)
   ↓
5. backend/app/middleware/security_middleware.py (apply middleware)
   ↓
6. backend/app/api/routes/*.py (load API routes)
   ↓
7. Application ready for requests
```

### Setup Flow
```
1. quick_setup.py (initial setup)
   ↓
2. security_setup_simple.py (security configuration)
   ↓
3. scripts/load_sample_data.py (load sample data)
   ↓
4. main.py (start application)
```

### Widget Integration Flow
```
1. demo.html (standalone demo)
   ↓
2. frontend/src/components/ChatWidget.jsx (React widget)
   ↓
3. backend/app/api/routes/chat.py (chat API)
   ↓
4. backend/app/services/rag_service.py (AI processing)
   ↓
5. Response sent back to widget
```

## 🎯 Key File Relationships

### Security System
- `backend/app/core/encryption.py` ← → `backend/app/core/security_enhanced.py`
- `backend/app/middleware/security_middleware.py` ← → `backend/app/api/routes/security.py`
- `data/security/` (stores encryption keys) ← → All security modules

### Database System
- `backend/app/core/database.py` ← → `backend/app/models/security_models.py`
- `backend/app/api/routes/auth.py` ← → `backend/app/api/routes/admin.py`
- Supabase database ← → All API routes

### Frontend Integration
- `demo.html` ← → `main.py` (API calls)
- `frontend/src/components/ChatWidget.jsx` ← → `backend/app/api/routes/chat.py`
- Widget embeds ← → College websites

### Multilingual Support
- `backend/app/services/rag_service.py` ← → Language detection and translation
- All API routes ← → Language parameter support
- `data/documents/` ← → Multilingual document storage

## 📊 File Statistics

| Category | Count | Total Size (approx.) |
|----------|-------|---------------------|
| Documentation | 8 files | ~50KB |
| Configuration | 6 files | ~10KB |
| Backend Code | 15+ files | ~100KB |
| Frontend Code | 5+ files | ~30KB |
| Dashboard Code | 3 files | ~40KB |
| Utility Scripts | 8 files | ~20KB |
| Docker Files | 3 files | ~5KB |
| **Total** | **48+ files** | **~255KB** |

## 🔍 File Maintenance

### Regular Updates Needed
- `requirements.txt` - Update dependencies
- `docs/` files - Update documentation
- `data/documents/` - Add new FAQ content
- `logs/` - Rotate log files

### Security Maintenance
- `data/security/` - Rotate encryption keys
- `backend/app/core/security_enhanced.py` - Update security policies
- `backend/app/middleware/security_middleware.py` - Update middleware rules

### Performance Monitoring
- `logs/app.log` - Monitor application logs
- `logs/security/` - Monitor security events
- Database tables - Monitor performance metrics

## 🎯 File Organization Benefits

### For Developers
- **Clear separation** of concerns
- **Modular architecture** for easy maintenance
- **Comprehensive documentation** for onboarding
- **Automated setup** scripts for quick deployment

### For System Administrators
- **Centralized configuration** management
- **Security-focused** file organization
- **Log aggregation** for monitoring
- **Docker containerization** for deployment

### For End Users
- **Interactive demo** for testing
- **Multiple dashboard** options for different roles
- **Widget integration** for seamless embedding
- **Comprehensive API** for custom integrations

## 🚀 Future File Additions

### Planned Additions
- `tests/` - Unit and integration tests
- `monitoring/` - Application monitoring scripts
- `backup/` - Automated backup scripts
- `analytics/` - Analytics and reporting tools
- `mobile/` - Mobile app components
- `api-docs/` - Enhanced API documentation

### Integration Files
- `integrations/wordpress/` - WordPress plugin files
- `integrations/moodle/` - Moodle integration
- `integrations/teams/` - Microsoft Teams integration
- `integrations/slack/` - Slack integration

---

**This file structure provides a solid foundation for a production-ready, scalable, and maintainable campus chatbot solution! 🎓**
