# LACBOT Maintenance Guide

This guide is designed for student volunteers and system administrators to maintain and update the LACBOT system.

## Table of Contents

1. [Daily Maintenance Tasks](#daily-maintenance-tasks)
2. [Weekly Maintenance Tasks](#weekly-maintenance-tasks)
3. [Monthly Maintenance Tasks](#monthly-maintenance-tasks)
4. [Content Management](#content-management)
5. [User Management](#user-management)
6. [System Monitoring](#system-monitoring)
7. [Troubleshooting Guide](#troubleshooting-guide)
8. [Emergency Procedures](#emergency-procedures)

## Daily Maintenance Tasks

### 1. System Health Check (5 minutes)
```bash
# Check if all services are running
docker-compose ps

# Check system resources
docker stats

# Verify API health
curl http://localhost:8000/health
```

### 2. Review Flagged Messages (10-15 minutes)
1. Log into Volunteer Dashboard
2. Check messages requiring human intervention
3. Review low-confidence responses
4. Take appropriate actions:
   - Provide better responses
   - Escalate complex queries
   - Add to FAQ if recurring

### 3. Monitor Error Logs (5 minutes)
```bash
# Check recent errors
tail -n 100 logs/app.log | grep ERROR

# Check for failed API calls
tail -n 100 logs/app.log | grep "500"
```

### 4. Backup Verification (2 minutes)
- Verify daily backups are running
- Check backup file sizes and dates
- Ensure backup storage has sufficient space

## Weekly Maintenance Tasks

### 1. Performance Analysis (30 minutes)
1. **Review Analytics Dashboard**
   - Check response times
   - Analyze user satisfaction scores
   - Review language usage patterns

2. **Identify Improvement Areas**
   - Common unanswered questions
   - Low-confidence responses
   - User feedback trends

### 2. Content Updates (1 hour)
1. **Update FAQs**
   - Add new frequently asked questions
   - Update outdated information
   - Improve existing answers

2. **Review Documents**
   - Check for policy changes
   - Update contact information
   - Add new institutional documents

### 3. User Management (30 minutes)
1. **Review New Users**
   - Check for suspicious accounts
   - Verify volunteer applications
   - Update user roles as needed

2. **Clean Up Inactive Users**
   - Archive old accounts
   - Remove test accounts
   - Update user preferences

### 4. Security Review (15 minutes)
```bash
# Check for security updates
docker-compose pull

# Review access logs
grep "401\|403" logs/access.log

# Verify SSL certificates
openssl x509 -in ssl/cert.pem -text -noout | grep "Not After"
```

## Monthly Maintenance Tasks

### 1. Comprehensive System Review (2 hours)
1. **Performance Metrics**
   - Review monthly usage statistics
   - Analyze growth trends
   - Plan capacity upgrades

2. **Content Audit**
   - Review all FAQ entries
   - Check document relevance
   - Update outdated information

3. **User Feedback Analysis**
   - Compile monthly feedback report
   - Identify improvement opportunities
   - Plan system enhancements

### 2. Database Maintenance (1 hour)
```bash
# Database optimization
python scripts/optimize_database.py

# Clean up old logs
python scripts/cleanup_logs.py

# Update statistics
python scripts/update_statistics.py
```

### 3. Model Updates (1 hour)
1. **Check for Model Updates**
   - Review Hugging Face model releases
   - Test new model versions
   - Update if performance improves

2. **Retrain Embeddings**
   - Add new documents to vector store
   - Update embeddings for changed content
   - Test retrieval accuracy

### 4. Documentation Updates (30 minutes)
- Update user guides
- Revise FAQ entries
- Document new procedures

## Content Management

### Adding New FAQs

#### Method 1: Through Admin Dashboard
1. Log into Super User Dashboard
2. Navigate to FAQ Management
3. Click "Create New FAQ"
4. Fill in required fields:
   - Question (in multiple languages)
   - Answer (detailed and helpful)
   - Category (fees, academics, etc.)
   - Priority (1-5, 5 being highest)
   - Language

#### Method 2: Bulk Import
```bash
# Prepare JSON file with new FAQs
python scripts/import_faqs.py data/new_faqs.json
```

### Updating Existing Content
1. **Identify Outdated Content**
   - Check user feedback
   - Review low-confidence responses
   - Monitor search queries

2. **Update Process**
   - Edit FAQ in dashboard
   - Test with sample queries
   - Monitor improvement in confidence scores

### Document Management
```bash
# Add new documents
python scripts/add_document.py --file "new_policy.pdf" --category "policies"

# Update existing documents
python scripts/update_document.py --id "doc_123" --file "updated_policy.pdf"

# Remove outdated documents
python scripts/remove_document.py --id "doc_123"
```

## User Management

### Volunteer Management

#### Adding New Volunteers
1. **Receive Application**
   - Review volunteer application
   - Verify credentials
   - Conduct brief interview

2. **Create Account**
   ```bash
   # Create volunteer account
   python scripts/create_user.py \
     --email "volunteer@college.edu" \
     --role "volunteer" \
     --languages "en,hi"
   ```

3. **Training**
   - Provide system access
   - Conduct training session
   - Assign mentor volunteer

#### Managing Volunteer Access
- **Grant Permissions**: Update user role to "volunteer"
- **Revoke Access**: Change role to "user" or "inactive"
- **Monitor Activity**: Review volunteer dashboard usage

### Super User Management
```bash
# Create super user account
python scripts/create_user.py \
  --email "admin@college.edu" \
  --role "superuser" \
  --full-name "System Administrator"
```

## System Monitoring

### Key Metrics to Monitor

#### 1. Performance Metrics
- **Response Time**: Should be < 3 seconds
- **Uptime**: Target 99.9%
- **Error Rate**: Should be < 1%
- **Memory Usage**: Monitor for leaks

#### 2. Usage Metrics
- **Daily Active Users**
- **Messages per Day**
- **Language Distribution**
- **Platform Usage** (Web vs WhatsApp)

#### 3. Quality Metrics
- **Confidence Scores**: Average should be > 0.8
- **Human Intervention Rate**: Should be < 10%
- **User Satisfaction**: Target > 4.0/5.0

### Monitoring Tools
```bash
# Real-time monitoring
docker-compose logs -f backend

# Performance monitoring
htop
iotop

# Database monitoring
python scripts/db_health_check.py
```

### Alert Setup
Configure alerts for:
- High error rates (> 5%)
- Slow response times (> 10 seconds)
- Low disk space (< 1GB)
- High memory usage (> 90%)

## Troubleshooting Guide

### Common Issues and Solutions

#### 1. Chatbot Not Responding
**Symptoms**: No response to user messages
**Causes**: 
- API service down
- Model loading issues
- Database connection problems

**Solutions**:
```bash
# Check service status
docker-compose ps

# Restart services
docker-compose restart backend

# Check logs
docker-compose logs backend
```

#### 2. Low Confidence Scores
**Symptoms**: Many responses marked as requiring human intervention
**Causes**:
- Outdated knowledge base
- Poor quality training data
- Model performance issues

**Solutions**:
- Review and update FAQs
- Add missing information
- Retrain embeddings
- Consider model updates

#### 3. Slow Response Times
**Symptoms**: Users reporting slow chatbot responses
**Causes**:
- High server load
- Database performance issues
- Network problems

**Solutions**:
```bash
# Check resource usage
docker stats

# Optimize database
python scripts/optimize_database.py

# Scale up resources
docker-compose up -d --scale backend=2
```

#### 4. WhatsApp Integration Issues
**Symptoms**: WhatsApp messages not being processed
**Causes**:
- Webhook configuration issues
- Twilio account problems
- Network connectivity

**Solutions**:
```bash
# Test webhook
curl -X POST https://your-domain.com/api/webhook/whatsapp \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "From=whatsapp:+1234567890&Body=test"

# Check Twilio logs
# Log into Twilio console and review webhook logs
```

#### 5. Database Connection Issues
**Symptoms**: Database errors in logs
**Causes**:
- Supabase service issues
- Network connectivity
- Incorrect credentials

**Solutions**:
```bash
# Test database connection
python scripts/test_db_connection.py

# Check environment variables
echo $SUPABASE_URL
echo $SUPABASE_KEY

# Verify Supabase status
# Check Supabase status page
```

### Performance Optimization

#### 1. Database Optimization
```bash
# Analyze query performance
python scripts/analyze_queries.py

# Optimize indexes
python scripts/optimize_indexes.py

# Clean up old data
python scripts/cleanup_old_data.py
```

#### 2. Model Optimization
```bash
# Cache models
python scripts/cache_models.py

# Optimize embeddings
python scripts/optimize_embeddings.py

# Update model configurations
python scripts/update_model_config.py
```

#### 3. System Optimization
```bash
# Clear system caches
docker system prune -f

# Optimize Docker images
docker image prune -f

# Review resource allocation
docker-compose config
```

## Emergency Procedures

### System Down Emergency

#### 1. Immediate Response (0-5 minutes)
```bash
# Check service status
docker-compose ps

# Quick restart attempt
docker-compose restart

# Check critical logs
docker-compose logs --tail=50 backend
```

#### 2. Escalation (5-15 minutes)
- Contact system administrator
- Check external service status (Supabase, Twilio)
- Notify users if extended downtime expected

#### 3. Recovery (15+ minutes)
- Follow disaster recovery procedures
- Restore from backup if necessary
- Verify all services before declaring resolved

### Security Incident Response

#### 1. Immediate Actions
- Change all passwords
- Revoke compromised API keys
- Review access logs
- Isolate affected systems

#### 2. Investigation
- Identify scope of breach
- Document evidence
- Notify relevant authorities
- Prepare incident report

#### 3. Recovery
- Patch vulnerabilities
- Update security measures
- Restore from clean backup
- Conduct security audit

### Data Loss Prevention
```bash
# Daily backup verification
python scripts/verify_backup.py

# Test restore procedure
python scripts/test_restore.py

# Monitor backup storage
df -h /backup
```

## Maintenance Schedule

### Daily (5-10 minutes)
- [ ] Health check
- [ ] Review flagged messages
- [ ] Check error logs
- [ ] Verify backups

### Weekly (1-2 hours)
- [ ] Performance analysis
- [ ] Content updates
- [ ] User management
- [ ] Security review

### Monthly (4-6 hours)
- [ ] Comprehensive system review
- [ ] Database maintenance
- [ ] Model updates
- [ ] Documentation updates

### Quarterly (1-2 days)
- [ ] Full security audit
- [ ] Disaster recovery testing
- [ ] Performance optimization
- [ ] User training updates

## Contact Information

### Internal Contacts
- **System Administrator**: admin@college.edu
- **Technical Lead**: tech-lead@college.edu
- **Volunteer Coordinator**: volunteers@college.edu

### External Support
- **Supabase Support**: support@supabase.com
- **Twilio Support**: help@twilio.com
- **Hugging Face Support**: support@huggingface.co

### Emergency Contacts
- **24/7 Emergency**: +1-XXX-XXX-XXXX
- **Escalation Email**: emergency@college.edu

## Documentation Updates

This maintenance guide should be updated:
- After major system changes
- When new procedures are added
- Based on volunteer feedback
- Quarterly review and update

### Version History
- **v1.0**: Initial maintenance guide
- **v1.1**: Added emergency procedures
- **v1.2**: Updated troubleshooting section

---

**Remember**: Regular maintenance is crucial for system reliability and user satisfaction. When in doubt, always consult with the system administrator before making changes.
