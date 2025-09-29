# 🎓 LACBOT - Comprehensive Setup and Integration Guide

This document provides detailed, step-by-step instructions for setting up, configuring, and integrating LACBOT across all platforms.

## 📑 Table of Contents

1. [User Roles and Access Control](#user-roles-and-access-control)
2. [Integrating LACBOT as a Website Widget](#integrating-lacbot-as-a-website-widget)
3. [WhatsApp Integration and Notifications](#whatsapp-integration-and-notifications)
4. [API Documentation](#api-documentation)
5. [Deployment Guide](#deployment-guide)
6. [Troubleshooting](#troubleshooting)

---

## 👥 User Roles and Access Control

### Role Definitions

#### 1. Super User (`super_user`)
- **Full system access**
- Manage all users and settings
- View all conversations and analytics
- Upload and manage documents
- Configure system settings
- Access security logs and audit trails

#### 2. Volunteer (`volunteer`)
- **Moderated access**
- Monitor conversations requiring human intervention
- Update FAQ entries
- Provide human support when needed
- View conversation analytics
- Cannot access user management or security logs

#### 3. Normal User (`normal_user`)
- **Limited access**
- Chat with the bot
- View their own conversation history
- Submit feedback
- Update language preferences
- Cannot access admin features

### Setting Up User Roles

#### Create Initial Super User

```sql
-- Insert initial super user (replace with your email)
INSERT INTO users (email, password_hash, role) VALUES (
    'admin@yourcampus.edu',
    '$2b$12$your_bcrypt_hash_here', -- Use a proper bcrypt hash
    'super_user'
);
```

#### Role Management API

```bash
# Create a new user with specific role
curl -X POST http://localhost:8000/api/admin/users \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your_jwt_token" \
  -d '{
    "email": "volunteer@campus.edu",
    "password": "secure_password",
    "role": "volunteer"
  }'

# Update user role
curl -X PUT http://localhost:8000/api/admin/users/user_id \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your_jwt_token" \
  -d '{"role": "super_user"}'
```

### Dashboard Access

#### Super User Dashboard
- **URL**: http://localhost:8501
- **Features**:
  - User management
  - System analytics
  - Security monitoring
  - Content management
  - Backup and restore

#### Volunteer Dashboard
- **URL**: http://localhost:8502
- **Features**:
  - Conversation monitoring
  - FAQ management
  - Human intervention queue
  - Basic analytics

#### Normal User Dashboard
- **URL**: http://localhost:8503
- **Features**:
  - Chat history
  - Language preferences
  - Feedback submission
  - Profile settings

---

## 🌐 Integrating LACBOT as a Website Widget

### Method 1: Direct Embedding (Recommended)

#### Step 1: Create Widget HTML

Create a file `widget.html`:

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>LACBOT Widget</title>
    <style>
        #lacbot-widget {
            position: fixed;
            bottom: 20px;
            right: 20px;
            width: 350px;
            height: 500px;
            background: white;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            display: none;
            flex-direction: column;
            z-index: 10000;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        }
        
        .widget-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 15px;
            border-radius: 15px 15px 0 0;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .widget-messages {
            flex: 1;
            padding: 15px;
            overflow-y: auto;
            background: #f8f9fa;
        }
        
        .widget-input {
            padding: 15px;
            border-top: 1px solid #e9ecef;
            display: flex;
            gap: 10px;
        }
        
        .widget-input input {
            flex: 1;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 20px;
            outline: none;
        }
        
        .widget-input button {
            background: #667eea;
            color: white;
            border: none;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            cursor: pointer;
        }
        
        .chat-toggle {
            position: fixed;
            bottom: 20px;
            right: 20px;
            width: 60px;
            height: 60px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border: none;
            border-radius: 50%;
            color: white;
            font-size: 24px;
            cursor: pointer;
            box-shadow: 0 4px 15px rgba(0,0,0,0.2);
            z-index: 10001;
        }
        
        .message {
            margin: 10px 0;
            padding: 10px 15px;
            border-radius: 15px;
            max-width: 80%;
        }
        
        .message.user {
            background: #667eea;
            color: white;
            margin-left: auto;
            border-bottom-right-radius: 5px;
        }
        
        .message.bot {
            background: white;
            border: 1px solid #e9ecef;
            margin-right: auto;
            border-bottom-left-radius: 5px;
        }
    </style>
</head>
<body>
    <!-- Chat Toggle Button -->
    <button class="chat-toggle" onclick="toggleWidget()">💬</button>
    
    <!-- Chat Widget -->
    <div id="lacbot-widget">
        <div class="widget-header">
            <div>
                <strong>🎓 LACBOT</strong>
                <div style="font-size: 12px;">Campus Assistant</div>
            </div>
            <button onclick="toggleWidget()" style="background: none; border: none; color: white; font-size: 18px;">✕</button>
        </div>
        
        <div class="widget-messages" id="messages">
            <div class="message bot">
                Hello! I'm LACBOT, your campus assistant. How can I help you today?
            </div>
        </div>
        
        <div class="widget-input">
            <input type="text" id="messageInput" placeholder="Type your message..." onkeypress="handleKeyPress(event)">
            <button onclick="sendMessage()">➤</button>
        </div>
    </div>

    <script>
        const API_BASE_URL = 'http://localhost:8000/api';
        let isOpen = false;
        
        function toggleWidget() {
            const widget = document.getElementById('lacbot-widget');
            isOpen = !isOpen;
            widget.style.display = isOpen ? 'flex' : 'none';
        }
        
        function handleKeyPress(event) {
            if (event.key === 'Enter') {
                sendMessage();
            }
        }
        
        async function sendMessage() {
            const input = document.getElementById('messageInput');
            const message = input.value.trim();
            if (!message) return;
            
            // Add user message
            addMessage(message, 'user');
            input.value = '';
            
            try {
                const response = await fetch(`${API_BASE_URL}/chat/message`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ message, language: 'en' })
                });
                
                const data = await response.json();
                addMessage(data.response, 'bot');
            } catch (error) {
                addMessage('Sorry, I encountered an error. Please try again.', 'bot');
            }
        }
        
        function addMessage(content, type) {
            const messages = document.getElementById('messages');
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${type}`;
            messageDiv.textContent = content;
            messages.appendChild(messageDiv);
            messages.scrollTop = messages.scrollHeight;
        }
    </script>
</body>
</html>
```

#### Step 2: Embed in Your Website

**For WordPress:**
1. Go to **Appearance > Theme Editor**
2. Edit `footer.php`
3. Add before `</body>`:
```html
<iframe src="http://localhost:8000/widget.html" 
        style="position: fixed; bottom: 0; right: 0; width: 350px; height: 500px; border: none; z-index: 9999;">
</iframe>
```

**For Custom Websites:**
```html
<!-- Add to your HTML before </body> -->
<script>
    // Load LACBOT widget
    (function() {
        const script = document.createElement('script');
        script.src = 'http://localhost:8000/static/widget.js';
        script.async = true;
        document.head.appendChild(script);
    })();
</script>
```

### Method 2: WordPress Plugin

Create `lacbot-widget-plugin.php`:

```php
<?php
/**
 * Plugin Name: LACBOT Campus Chatbot Widget
 * Description: Integrates LACBOT multilingual chatbot into your WordPress site
 * Version: 1.0.0
 * Author: Your Name
 */

class LACBOTWidget {
    
    public function __construct() {
        add_action('wp_footer', array($this, 'add_widget_script'));
        add_action('admin_menu', array($this, 'add_admin_menu'));
        add_action('admin_init', array($this, 'register_settings'));
    }
    
    public function add_widget_script() {
        $api_url = get_option('lacbot_api_url', 'http://localhost:8000');
        $enabled = get_option('lacbot_enabled', false);
        
        if ($enabled) {
            echo '<script>
                window.LACBOT_CONFIG = {
                    apiUrl: "' . esc_js($api_url) . '",
                    position: "bottom-right",
                    theme: "default"
                };
            </script>';
            echo '<script src="' . esc_url($api_url) . '/static/widget.js" async></script>';
        }
    }
    
    public function add_admin_menu() {
        add_options_page(
            'LACBOT Settings',
            'LACBOT Chatbot',
            'manage_options',
            'lacbot-settings',
            array($this, 'admin_page')
        );
    }
    
    public function register_settings() {
        register_setting('lacbot_settings', 'lacbot_api_url');
        register_setting('lacbot_settings', 'lacbot_enabled');
    }
    
    public function admin_page() {
        ?>
        <div class="wrap">
            <h1>LACBOT Settings</h1>
            <form method="post" action="options.php">
                <?php settings_fields('lacbot_settings'); ?>
                <table class="form-table">
                    <tr>
                        <th scope="row">Enable LACBOT</th>
                        <td>
                            <input type="checkbox" name="lacbot_enabled" value="1" 
                                   <?php checked(1, get_option('lacbot_enabled'), true); ?> />
                        </td>
                    </tr>
                    <tr>
                        <th scope="row">API URL</th>
                        <td>
                            <input type="url" name="lacbot_api_url" 
                                   value="<?php echo esc_attr(get_option('lacbot_api_url')); ?>" 
                                   class="regular-text" />
                        </td>
                    </tr>
                </table>
                <?php submit_button(); ?>
            </form>
        </div>
        <?php
    }
}

new LACBOTWidget();
?>
```

---

## 📱 WhatsApp Integration and Notifications

### Step 1: Set Up Twilio WhatsApp

1. **Create Twilio Account**:
   - Go to [Twilio Console](https://console.twilio.com/)
   - Sign up for a free account
   - Verify your phone number

2. **Enable WhatsApp Sandbox**:
   - Go to **Messaging > Try it out > Send a WhatsApp message**
   - Follow instructions to enable sandbox
   - Note your WhatsApp sandbox number

3. **Get Credentials**:
   - Account SID: Found in Twilio Console dashboard
   - Auth Token: Found in Twilio Console dashboard
   - WhatsApp Number: Provided in sandbox setup

### Step 2: Configure WhatsApp Webhook

```bash
# Update your .env file
TWILIO_ACCOUNT_SID=your_account_sid
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_WHATSAPP_NUMBER=whatsapp:+14155238886
```

### Step 3: Test WhatsApp Integration

```bash
# Test webhook endpoint
curl -X POST http://localhost:8000/api/webhook/whatsapp \
  -H "Content-Type: application/json" \
  -d '{
    "From": "whatsapp:+1234567890",
    "Body": "Hello LACBOT",
    "MessageSid": "test_message_id"
  }'
```

### Step 4: Set Up Notifications

#### Email Notifications

Create `notifications/email_service.py`:

```python
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

class EmailNotificationService:
    def __init__(self):
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.email = os.getenv('NOTIFICATION_EMAIL')
        self.password = os.getenv('NOTIFICATION_PASSWORD')
    
    def send_notification(self, to_email, subject, message):
        try:
            msg = MIMEMultipart()
            msg['From'] = self.email
            msg['To'] = to_email
            msg['Subject'] = subject
            
            msg.attach(MIMEText(message, 'plain'))
            
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.email, self.password)
            
            text = msg.as_string()
            server.sendmail(self.email, to_email, text)
            server.quit()
            
            return True
        except Exception as e:
            print(f"Email notification failed: {e}")
            return False

# Usage
email_service = EmailNotificationService()
email_service.send_notification(
    'admin@campus.edu',
    'LACBOT: Human Intervention Required',
    'A conversation requires human intervention. Please check the volunteer dashboard.'
)
```

#### Push Notifications

Create `notifications/push_service.py`:

```python
import requests
import json

class PushNotificationService:
    def __init__(self):
        self.fcm_server_key = os.getenv('FCM_SERVER_KEY')
        self.fcm_url = 'https://fcm.googleapis.com/fcm/send'
    
    def send_to_volunteers(self, title, body, data=None):
        # Get volunteer FCM tokens from database
        volunteer_tokens = self.get_volunteer_tokens()
        
        for token in volunteer_tokens:
            payload = {
                'to': token,
                'notification': {
                    'title': title,
                    'body': body,
                    'icon': '/static/icon.png'
                },
                'data': data or {}
            }
            
            headers = {
                'Authorization': f'key={self.fcm_server_key}',
                'Content-Type': 'application/json'
            }
            
            try:
                response = requests.post(self.fcm_url, 
                                       data=json.dumps(payload), 
                                       headers=headers)
                print(f"Push notification sent: {response.status_code}")
            except Exception as e:
                print(f"Push notification failed: {e}")

# Usage
push_service = PushNotificationService()
push_service.send_to_volunteers(
    'LACBOT Alert',
    'New conversation requires human intervention',
    {'conversation_id': '123', 'priority': 'high'}
)
```

### Step 5: Automated Notification Rules

Create `notifications/rules.py`:

```python
class NotificationRules:
    def __init__(self):
        self.email_service = EmailNotificationService()
        self.push_service = PushNotificationService()
    
    def check_conversation_rules(self, conversation):
        # Rule 1: High priority queries
        if conversation.get('priority') == 'high':
            self.email_service.send_notification(
                'admin@campus.edu',
                'High Priority Query',
                f'Conversation {conversation["id"]} marked as high priority'
            )
        
        # Rule 2: Multiple failed responses
        if conversation.get('failed_responses', 0) > 3:
            self.push_service.send_to_volunteers(
                'LACBOT: Multiple Failed Responses',
                f'Conversation {conversation["id"]} needs human intervention'
            )
        
        # Rule 3: Long conversation duration
        if conversation.get('duration_minutes', 0) > 30:
            self.email_service.send_notification(
                'volunteer@campus.edu',
                'Long Conversation Alert',
                f'Conversation {conversation["id"]} is taking longer than expected'
            )
```

---

## 📚 API Documentation

### Authentication Endpoints

#### Register User
```bash
POST /api/auth/register
Content-Type: application/json

{
  "email": "user@campus.edu",
  "password": "secure_password",
  "role": "normal_user"
}
```

#### Login
```bash
POST /api/auth/login
Content-Type: application/json

{
  "email": "user@campus.edu",
  "password": "secure_password"
}

Response:
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

### Chat Endpoints

#### Send Message
```bash
POST /api/chat/message
Authorization: Bearer your_jwt_token
Content-Type: application/json

{
  "message": "When is the fee deadline?",
  "language": "en",
  "session_id": "optional_session_id"
}

Response:
{
  "response": "The deadline for semester fee payment is March 15, 2024.",
  "confidence_score": 0.95,
  "language": "en",
  "requires_human": false,
  "source_documents": [],
  "session_id": "generated_session_id",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

#### Get Conversation History
```bash
GET /api/chat/conversations
Authorization: Bearer your_jwt_token

Response:
{
  "conversations": [
    {
      "id": "conv_123",
      "started_at": "2024-01-01T10:00:00Z",
      "total_messages": 5,
      "language": "en",
      "satisfaction_score": 4
    }
  ]
}
```

### Admin Endpoints

#### Manage Users
```bash
# Get all users (Super User only)
GET /api/admin/users
Authorization: Bearer your_jwt_token

# Create user
POST /api/admin/users
Authorization: Bearer your_jwt_token
Content-Type: application/json

{
  "email": "newuser@campus.edu",
  "password": "password123",
  "role": "volunteer"
}

# Update user
PUT /api/admin/users/{user_id}
Authorization: Bearer your_jwt_token
Content-Type: application/json

{
  "role": "super_user",
  "is_active": true
}
```

#### Manage FAQs
```bash
# Get all FAQs
GET /api/admin/faqs
Authorization: Bearer your_jwt_token

# Create FAQ
POST /api/admin/faqs
Authorization: Bearer your_jwt_token
Content-Type: application/json

{
  "question": "What are the library hours?",
  "answer": "The library is open Monday-Friday 8AM-10PM, Saturday 9AM-6PM, Sunday 10AM-5PM.",
  "category": "library",
  "language": "en",
  "priority": 3
}

# Update FAQ
PUT /api/admin/faqs/{faq_id}
Authorization: Bearer your_jwt_token
Content-Type: application/json

{
  "answer": "Updated answer text",
  "priority": 5
}
```

### Webhook Endpoints

#### WhatsApp Webhook
```bash
POST /api/webhook/whatsapp
Content-Type: application/x-www-form-urlencoded

From=whatsapp:+1234567890&Body=Hello&MessageSid=SM123
```

#### Telegram Webhook (Optional)
```bash
POST /api/webhook/telegram
Content-Type: application/json

{
  "update_id": 123456,
  "message": {
    "message_id": 123,
    "from": {"id": 123456, "first_name": "John"},
    "chat": {"id": 123456, "type": "private"},
    "date": 1640995200,
    "text": "Hello LACBOT"
  }
}
```

---

## 🚀 Deployment Guide

### Local Development

```bash
# Start all services
python main.py

# Start dashboards (in separate terminals)
streamlit run dashboards/super_user_dashboard.py --server.port 8501
streamlit run dashboards/volunteer_dashboard.py --server.port 8502
streamlit run dashboards/normal_user_dashboard.py --server.port 8503
```

### Docker Deployment

#### Build and Run
```bash
# Build the application
docker-compose build

# Run in production mode
docker-compose -f docker-compose.prod.yml up -d

# Check logs
docker-compose logs -f
```

#### Docker Compose Configuration
```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DEBUG=False
      - HOST=0.0.0.0
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - app
    restart: unless-stopped

  redis:
    image: redis:alpine
    restart: unless-stopped

  postgres:
    image: postgres:13
    environment:
      POSTGRES_DB: lacbot
      POSTGRES_USER: lacbot
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped

volumes:
  postgres_data:
```

### Cloud Deployment

#### Railway Deployment
```bash
# Install Railway CLI
npm install -g @railway/cli

# Login to Railway
railway login

# Deploy
railway up
```

#### Render Deployment
1. Connect your GitHub repository to Render
2. Create a new Web Service
3. Configure build and start commands:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python main.py`
4. Set environment variables in Render dashboard

#### AWS Deployment
```bash
# Using AWS Elastic Beanstalk
pip install awsebcli
eb init
eb create production
eb deploy
```

### SSL/HTTPS Setup

#### Using Let's Encrypt
```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx

# Generate certificate
sudo certbot --nginx -d yourdomain.com

# Auto-renewal
sudo crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

#### Using Cloudflare
1. Add your domain to Cloudflare
2. Update nameservers
3. Enable SSL/TLS encryption
4. Configure proxy settings

---

## 🔧 Troubleshooting

### Common Issues

#### 1. Port Already in Use
```bash
# Find process using port 8000
netstat -tulpn | grep :8000

# Kill process
sudo kill -9 <PID>

# Or use different port
uvicorn main:app --port 8001
```

#### 2. Database Connection Issues
```bash
# Check Supabase connection
curl -H "apikey: your_supabase_key" \
     -H "Authorization: Bearer your_supabase_key" \
     https://your-project.supabase.co/rest/v1/users

# Test database connectivity
python -c "
import os
from supabase import create_client
url = os.getenv('SUPABASE_URL')
key = os.getenv('SUPABASE_KEY')
supabase = create_client(url, key)
print('Connection successful')
"
```

#### 3. Memory Issues
```bash
# Check memory usage
free -h

# Increase swap space
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

#### 4. SSL Certificate Issues
```bash
# Check certificate validity
openssl x509 -in /path/to/certificate.crt -text -noout

# Renew Let's Encrypt certificate
sudo certbot renew --dry-run
```

### Performance Optimization

#### Database Optimization
```sql
-- Add indexes for better performance
CREATE INDEX CONCURRENTLY idx_messages_created_at_desc 
ON messages(created_at DESC);

CREATE INDEX CONCURRENTLY idx_conversations_user_started 
ON conversations(user_id, started_at DESC);

-- Analyze tables
ANALYZE messages;
ANALYZE conversations;
ANALYZE faqs;
```

#### Application Optimization
```python
# Enable connection pooling
from sqlalchemy.pool import QueuePool

engine = create_engine(
    database_url,
    poolclass=QueuePool,
    pool_size=20,
    max_overflow=0
)

# Enable Redis caching
import redis
redis_client = redis.Redis(host='localhost', port=6379, db=0)

def get_cached_response(query):
    cached = redis_client.get(f"response:{hash(query)}")
    if cached:
        return json.loads(cached)
    return None
```

### Monitoring and Logging

#### Application Monitoring
```bash
# Install monitoring tools
pip install prometheus-client psutil

# Monitor system resources
python -c "
import psutil
print(f'CPU: {psutil.cpu_percent()}%')
print(f'Memory: {psutil.virtual_memory().percent}%')
print(f'Disk: {psutil.disk_usage(\"/\").percent}%')
"
```

#### Log Analysis
```bash
# View application logs
tail -f logs/app.log

# Monitor error logs
grep "ERROR" logs/app.log | tail -20

# Analyze performance
grep "slow_query" logs/app.log | wc -l
```

---

## 🤝 Contributing

### Development Setup

1. **Fork the repository**
2. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. **Make your changes**
4. **Run tests**
   ```bash
   python -m pytest tests/
   ```
5. **Commit your changes**
   ```bash
   git commit -m "Add your feature"
   ```
6. **Push to your fork**
   ```bash
   git push origin feature/your-feature-name
   ```
7. **Create a Pull Request**

### Code Standards

- Follow PEP 8 for Python code
- Use type hints for function parameters and return values
- Write comprehensive docstrings
- Add unit tests for new features
- Update documentation for API changes

### Testing

```bash
# Run all tests
python -m pytest

# Run with coverage
python -m pytest --cov=app

# Run specific test file
python -m pytest tests/test_chat.py

# Run with verbose output
python -m pytest -v
```

---

## 📞 Support and Contact

### Getting Help

- **GitHub Issues**: [Create an issue](https://github.com/yourusername/lacbot/issues)
- **Documentation**: Check the `docs/` folder for detailed guides
- **Email Support**: support@lacbot.edu
- **Community Forum**: [Join our Discord](https://discord.gg/lacbot)

### Professional Support

For enterprise deployments or custom integrations:
- **Email**: enterprise@lacbot.edu
- **Phone**: +1-555-LACBOT
- **Consultation**: Available for campus-wide implementations

---

## 📊 Project Status

- **Version**: 1.0.0
- **Last Updated**: January 2024
- **License**: MIT
- **Maintainer**: Campus Development Team

## 🏆 Acknowledgments

- **Hugging Face** for providing free multilingual models
- **Supabase** for the robust database and authentication platform
- **FastAPI** for the excellent Python web framework
- **Twilio** for WhatsApp integration capabilities
- **Open Source Community** for the amazing tools and libraries

---

**Built with ❤️ for educational institutions worldwide**

*LACBOT - Empowering campus communities through intelligent multilingual communication*

