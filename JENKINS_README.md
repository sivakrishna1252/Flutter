# 🚀 Jenkins CI/CD Deployment - README

## 📖 Overview

This repository contains a complete **Jenkins CI/CD pipeline** for automated deployment of the **Diet Planner Django API**. The pipeline automatically builds, tests, and deploys your application whenever you push code to GitHub.

![Jenkins Deployment Workflow](../jenkins_deployment_workflow_1769662914931.png)

---

## 📦 What's Included

### Documentation Files
- **`DEPLOYMENT_SUMMARY.md`** - Complete step-by-step deployment guide (START HERE!)
- **`JENKINS_DEPLOYMENT.md`** - Detailed 14-section comprehensive guide
- **`JENKINS_QUICK_REFERENCE.md`** - Quick commands and troubleshooting

### Configuration Files
- **`Jenkinsfile`** - CI/CD pipeline definition
- **`Dockerfile.production`** - Production-optimized Docker image
- **`docker-compose.production.yml`** - Production orchestration
- **`nginx.conf`** - Reverse proxy configuration

### Scripts
- **`jenkins_setup.sh`** - Automated Jenkins installation script

---

## 🎯 Quick Start (30 Minutes)

### Prerequisites
- Linux server (Ubuntu 20.04+ recommended)
- 2GB RAM minimum
- 20GB disk space
- Ports 8080 and 1513 open
- GitHub account

### Step 1: Install Jenkins (15 minutes)
```bash
# On your server
sudo bash jenkins_setup.sh
```

### Step 2: Configure Jenkins (10 minutes)
1. Access Jenkins: `http://your-server-ip:8080`
2. Install suggested plugins
3. Add credentials (SECRET_KEY, OPENAI_API_KEY, GitHub)
4. Create pipeline job

### Step 3: Deploy (5 minutes)
1. Push code to GitHub
2. Click "Build Now" in Jenkins
3. Wait for deployment to complete
4. Access API at `http://your-server-ip:1513`

**📚 For detailed instructions, see `DEPLOYMENT_SUMMARY.md`**

---

## 🔄 How It Works

### Automated Deployment Flow

```
Developer → GitHub → Jenkins → Docker → Production
    ↓          ↓         ↓         ↓         ↓
  Code      Webhook   Build     Deploy    Live!
  Push      Trigger   & Test   Container   API
```

### Pipeline Stages

1. **Checkout** - Clone code from GitHub
2. **Build** - Create Docker image
3. **Test** - Run Django tests
4. **Stop Old** - Stop previous container
5. **Deploy** - Start new container
6. **Health Check** - Verify deployment
7. **Cleanup** - Remove old images

**Total Time:** ~5-10 minutes per deployment

---

## 📋 Deployment Checklist

### Before First Deployment
- [ ] Server provisioned and accessible
- [ ] Jenkins installed (`jenkins_setup.sh`)
- [ ] Docker installed and running
- [ ] GitHub repository created
- [ ] Code pushed to GitHub
- [ ] Jenkins credentials configured
- [ ] Pipeline job created

### After First Deployment
- [ ] Container running (`docker ps`)
- [ ] API responding (`curl http://localhost:1513/api/schema/`)
- [ ] Swagger UI accessible
- [ ] Tests passing
- [ ] No errors in logs

---

## 🎓 Documentation Guide

### For First-Time Setup
1. **Start with:** `DEPLOYMENT_SUMMARY.md`
   - Complete walkthrough
   - Step-by-step instructions
   - Visual diagrams

2. **Reference:** `JENKINS_DEPLOYMENT.md`
   - Detailed explanations
   - Advanced configurations
   - Security best practices

3. **Quick Help:** `JENKINS_QUICK_REFERENCE.md`
   - Common commands
   - Troubleshooting
   - Checklists

### For Daily Operations
- **Quick Reference:** `JENKINS_QUICK_REFERENCE.md`
- **Troubleshooting:** Check "Common Issues" section
- **Monitoring:** Jenkins Dashboard + Docker logs

---

## 🔐 Security Features

### Built-in Security
✅ Secrets managed via Jenkins credentials  
✅ Non-root user in Docker container  
✅ Environment variables not in code  
✅ Automated security updates  
✅ Health monitoring  
✅ Automatic rollback on failure  

### Production Recommendations
- Generate new SECRET_KEY for production
- Set DEBUG=False (already configured)
- Configure ALLOWED_HOSTS with your domain
- Enable HTTPS with SSL certificate
- Setup firewall rules
- Regular backups

---

## 📊 Monitoring & Logs

### Check Deployment Status
```bash
# Jenkins build status
http://your-server-ip:8080

# Container status
docker ps

# Application logs
docker logs -f diet-planner-api

# Jenkins logs
sudo journalctl -u jenkins -f
```

### Health Checks
```bash
# API health
curl http://localhost:1513/api/schema/

# Container health
docker inspect diet-planner-api | grep Health

# Resource usage
docker stats diet-planner-api
```

---

## 🐛 Troubleshooting

### Common Issues

**Build Fails:**
```bash
# Check Jenkins logs
sudo journalctl -u jenkins -f

# Check Docker
docker ps
docker logs diet-planner-api
```

**Permission Denied:**
```bash
sudo usermod -aG docker jenkins
sudo systemctl restart jenkins
```

**Port Already in Use:**
```bash
docker stop diet-planner-api
docker rm diet-planner-api
```

**For more solutions, see:** `JENKINS_QUICK_REFERENCE.md`

---

## 🌐 Access Your Application

After successful deployment:

- **API Base:** `http://your-server-ip:1513`
- **Swagger UI:** `http://your-server-ip:1513/api/schema/swagger-ui/`
- **ReDoc:** `http://your-server-ip:1513/api/schema/redoc/`
- **Admin Panel:** `http://your-server-ip:1513/admin/`
- **Jenkins:** `http://your-server-ip:8080`

---

## 🔄 Continuous Deployment

### Automatic Deployment on Push

**Option 1: GitHub Webhook (Recommended)**
- Every push to GitHub triggers deployment
- Setup in GitHub → Settings → Webhooks
- Webhook URL: `http://your-server-ip:8080/github-webhook/`

**Option 2: Poll SCM (Already Configured)**
- Jenkins checks GitHub every 5 minutes
- Automatically builds if changes detected

### Manual Deployment
1. Go to Jenkins Dashboard
2. Click on `diet-planner-deployment`
3. Click "Build Now"

---

## 📈 Next Steps

### Immediate
1. Create superuser: `docker exec -it diet-planner-api python manage.py createsuperuser`
2. Test all API endpoints
3. Review deployment logs
4. Setup monitoring

### Short-term
1. Configure domain name
2. Install SSL certificate
3. Setup automated backups
4. Configure email notifications

### Long-term
1. Setup staging environment
2. Implement blue-green deployment
3. Add performance monitoring
4. Setup centralized logging

---

## 📚 Additional Resources

### Official Documentation
- [Jenkins Documentation](https://www.jenkins.io/doc/)
- [Docker Documentation](https://docs.docker.com/)
- [Django Deployment Guide](https://docs.djangoproject.com/en/4.2/howto/deployment/)

### Project Documentation
- [Project README](../README.md)
- [Alternative Deployments](../DEPLOYMENT.md)
- [Git Push Guide](../GIT_PUSH_GUIDE.md)

---

## 🤝 Support

### Getting Help
1. Check the documentation files
2. Review Jenkins console output
3. Check Docker logs
4. Review troubleshooting section

### Useful Commands
```bash
# Restart Jenkins
sudo systemctl restart jenkins

# Restart container
docker restart diet-planner-api

# View all logs
docker logs diet-planner-api
sudo journalctl -u jenkins -f
```

---

## ✅ Success Criteria

Your deployment is successful when:
- ✅ Jenkins build shows "SUCCESS"
- ✅ Container is running: `docker ps | grep diet-planner`
- ✅ API responds: `curl http://localhost:1513/api/schema/`
- ✅ Swagger UI loads in browser
- ✅ No errors in logs
- ✅ Tests are passing

---

## 🎉 You're Ready!

You now have:
- ✅ Fully automated CI/CD pipeline
- ✅ Automated testing before deployment
- ✅ Zero-downtime deployments
- ✅ Automatic rollback on failures
- ✅ Production-ready configuration
- ✅ Comprehensive documentation

### Your New Workflow:
```
1. Write code
2. git push
3. Jenkins automatically deploys
4. Your changes are live!
```

**Deployment time:** ~30 seconds after push! 🚀

---

## 📞 Quick Links

- **Start Here:** [DEPLOYMENT_SUMMARY.md](DEPLOYMENT_SUMMARY.md)
- **Complete Guide:** [JENKINS_DEPLOYMENT.md](JENKINS_DEPLOYMENT.md)
- **Quick Reference:** [JENKINS_QUICK_REFERENCE.md](JENKINS_QUICK_REFERENCE.md)
- **Project README:** [../README.md](../README.md)

---

**Happy Deploying! 🚀**

*Last Updated: January 2026*
