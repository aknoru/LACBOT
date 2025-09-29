# LACBOT Deployment Guide

This guide provides comprehensive instructions for deploying LACBOT in production environments.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Environment Setup](#environment-setup)
3. [Database Configuration](#database-configuration)
4. [API Configuration](#api-configuration)
5. [Deployment Options](#deployment-options)
6. [Production Configuration](#production-configuration)
7. [Monitoring & Maintenance](#monitoring--maintenance)
8. [Troubleshooting](#troubleshooting)

## Prerequisites

### System Requirements
- **CPU**: 4+ cores (8+ recommended for production)
- **RAM**: 8GB+ (16GB+ recommended)
- **Storage**: 50GB+ SSD
- **Network**: Stable internet connection with good bandwidth

### Software Requirements
- **Operating System**: Ubuntu 20.04+ / CentOS 8+ / Windows Server 2019+
- **Python**: 3.9+
- **Node.js**: 16+
- **Docker**: 20.10+ (for containerized deployment)
- **Nginx**: 1.18+ (for reverse proxy)
- **SSL Certificate**: Let's Encrypt or commercial certificate

### External Services
- **Supabase**: Database and authentication
- **Twilio**: WhatsApp integration (optional)
- **Domain Name**: For production deployment

## Environment Setup

### 1. Clone Repository
```bash
git clone <repository-url>
cd LACBOT
```

### 2. Run Setup Script
```bash
python setup.py
```

### 3. Configure Environment Variables
Edit the `.env` file with your production values:

```bash
# Database Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_supabase_anon_key
SUPABASE_SERVICE_KEY=your_supabase_service_key

# Security (Generate strong keys)
SECRET_KEY=your_strong_secret_key_here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# AI Model Configuration
HUGGINGFACE_API_TOKEN=your_huggingface_token
OPENAI_API_KEY=your_openai_api_key

# WhatsApp Integration
TWILIO_ACCOUNT_SID=your_twilio_account_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token
TWILIO_WHATSAPP_NUMBER=whatsapp:+14155238886

# Production Settings
DEBUG=False
HOST=0.0.0.0
PORT=8000
FRONTEND_URL=https://your-domain.com

# Rate Limiting
RATE_LIMIT_PER_MINUTE=60
RATE_LIMIT_BURST=100
```

## Database Configuration

### 1. Supabase Setup
1. Create a new project at [supabase.com](https://supabase.com)
2. Note down your project URL and API keys
3. Enable the `pgvector` extension for vector search
4. Run the database initialization script

### 2. Database Schema
The application will automatically create the required tables on first run. Key tables include:
- `users` - User accounts and authentication
- `conversations` - Chat conversations
- `messages` - Individual chat messages
- `documents` - Knowledge base documents
- `faqs` - Frequently asked questions
- `embeddings` - Vector embeddings for RAG

### 3. Sample Data
Load sample FAQs and documents:
```bash
python scripts/load_sample_data.py
```

## API Configuration

### 1. Hugging Face Setup
1. Create account at [huggingface.co](https://huggingface.co)
2. Generate API token
3. Add token to environment variables

### 2. WhatsApp Integration (Optional)
1. Create Twilio account
2. Set up WhatsApp sandbox
3. Configure webhook URL: `https://your-domain.com/api/webhook/whatsapp`

### 3. Language Models
The system uses these models by default:
- **Embedding**: `sentence-transformers/all-MiniLM-L6-v2`
- **Translation**: `facebook/nllb-200-distilled-600M`
- **LLM**: `microsoft/DialoGPT-medium` (free alternative)

## Deployment Options

### Option 1: Docker Deployment (Recommended)

#### 1. Build and Deploy
```bash
# Build all services
docker-compose build

# Start services
docker-compose up -d

# Check status
docker-compose ps
```

#### 2. Production Docker Compose
Create `docker-compose.prod.yml`:
```yaml
version: '3.8'

services:
  backend:
    build: ./backend
    environment:
      - DEBUG=False
      - SUPABASE_URL=${SUPABASE_URL}
      # ... other environment variables
    restart: unless-stopped
    deploy:
      resources:
        limits:
          memory: 2G
          cpus: '1.0'

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - backend
    restart: unless-stopped
```

### Option 2: Manual Deployment

#### 1. Backend Deployment
```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Run with Gunicorn
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

#### 2. Frontend Deployment
```bash
cd frontend

# Install dependencies
npm install

# Build for production
npm run build

# Serve with Nginx or serve the build directory
```

#### 3. Dashboard Deployment
```bash
cd dashboards

# Install dependencies
pip install -r requirements.txt

# Run Streamlit
streamlit run super_user_dashboard.py --server.port 8501 --server.address 0.0.0.0
streamlit run volunteer_dashboard.py --server.port 8502 --server.address 0.0.0.0
```

### Option 3: Cloud Deployment

#### AWS Deployment
1. **EC2 Instance**: Launch Ubuntu 20.04 instance
2. **RDS**: Use managed PostgreSQL (optional, Supabase recommended)
3. **S3**: Store static files and documents
4. **CloudFront**: CDN for global distribution
5. **Application Load Balancer**: For high availability

#### Railway Deployment
1. Connect your GitHub repository
2. Configure environment variables
3. Deploy automatically on push

#### Render Deployment
1. Create new web service
2. Connect repository
3. Configure build and start commands
4. Set environment variables

## Production Configuration

### 1. SSL/TLS Configuration
```nginx
# nginx.conf
server {
    listen 443 ssl http2;
    server_name your-domain.com;
    
    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;
    
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;
    ssl_prefer_server_ciphers off;
    
    # HSTS
    add_header Strict-Transport-Security "max-age=63072000" always;
}
```

### 2. Security Headers
```nginx
add_header X-Frame-Options DENY;
add_header X-Content-Type-Options nosniff;
add_header X-XSS-Protection "1; mode=block";
add_header Referrer-Policy "strict-origin-when-cross-origin";
```

### 3. Rate Limiting
```nginx
limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
limit_req_zone $binary_remote_addr zone=chat:10m rate=5r/s;
```

### 4. Monitoring Setup
```bash
# Install monitoring tools
pip install prometheus-client
pip install grafana-api

# Set up log rotation
sudo logrotate -f /etc/logrotate.conf
```

## Monitoring & Maintenance

### 1. Health Checks
- **API Health**: `GET /health`
- **Database Health**: Check Supabase dashboard
- **Model Health**: Monitor response times

### 2. Logging
```python
# Configure logging
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/app.log'),
        logging.StreamHandler()
    ]
)
```

### 3. Performance Monitoring
- Monitor response times
- Track memory usage
- Monitor API rate limits
- Check database performance

### 4. Backup Strategy
- **Database**: Supabase automatic backups
- **Documents**: Regular backup to S3 or local storage
- **Configuration**: Version control with Git

### 5. Update Procedure
```bash
# 1. Backup current deployment
docker-compose down
cp -r data data_backup_$(date +%Y%m%d)

# 2. Pull latest changes
git pull origin main

# 3. Update dependencies
docker-compose build

# 4. Deploy updates
docker-compose up -d

# 5. Verify deployment
curl http://localhost:8000/health
```

## Troubleshooting

### Common Issues

#### 1. Database Connection Issues
```bash
# Check Supabase connection
curl -H "apikey: YOUR_KEY" https://your-project.supabase.co/rest/v1/

# Verify environment variables
echo $SUPABASE_URL
```

#### 2. Model Loading Issues
```bash
# Check Hugging Face token
python -c "from transformers import AutoTokenizer; print('Token valid')"

# Clear model cache
rm -rf ~/.cache/huggingface/
```

#### 3. WhatsApp Integration Issues
```bash
# Test webhook
curl -X POST https://your-domain.com/api/webhook/whatsapp \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "From=whatsapp:+1234567890&Body=test"
```

#### 4. Performance Issues
```bash
# Monitor resource usage
docker stats

# Check logs
docker-compose logs -f backend

# Profile application
python -m cProfile -o profile.stats app/main.py
```

### Support Contacts
- **Technical Issues**: Create GitHub issue
- **Documentation**: Check docs/ folder
- **Emergency**: Contact system administrator

## Cost Optimization

### 1. Model Selection
- Use smaller, faster models for development
- Scale up models based on usage
- Consider model caching strategies

### 2. Infrastructure
- Use spot instances for development
- Implement auto-scaling
- Monitor and optimize resource usage

### 3. API Usage
- Implement caching for frequent queries
- Use rate limiting to prevent abuse
- Monitor API costs and usage

## Security Checklist

- [ ] SSL/TLS certificates configured
- [ ] Environment variables secured
- [ ] Database access restricted
- [ ] API rate limiting enabled
- [ ] Input validation implemented
- [ ] Authentication required for admin functions
- [ ] Regular security updates applied
- [ ] Backup and recovery tested
- [ ] Monitoring and alerting configured
- [ ] Access logs reviewed regularly

## Expected Performance

### Response Times
- **Simple Queries**: < 2 seconds
- **Complex Queries**: < 5 seconds
- **Model Loading**: < 30 seconds (first time)

### Scalability
- **Concurrent Users**: 1000+
- **Messages per Minute**: 500+
- **Storage**: Scales with usage

### Availability
- **Uptime Target**: 99.9%
- **Recovery Time**: < 5 minutes
- **Backup Frequency**: Daily

---

For additional support, please refer to the main documentation or contact the development team.
