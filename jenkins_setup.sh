#!/bin/bash

# ============================================================================
# Jenkins Installation Script for Ubuntu/Debian
# ============================================================================
# This script automates the installation of Jenkins, Docker, and required tools
# Run with: sudo bash jenkins_setup.sh
# ============================================================================

set -e  # Exit on error

echo "============================================================================"
echo "🚀 Starting Jenkins Installation for Diet Planner API"
echo "============================================================================"

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "❌ Please run as root (use sudo)"
    exit 1
fi

# Update system
echo ""
echo "📦 Updating system packages..."
apt update && apt upgrade -y

# Install Java (required for Jenkins)
echo ""
echo "☕ Installing Java..."
apt install -y openjdk-11-jdk

# Verify Java installation
java -version
echo "✅ Java installed successfully"

# Install Jenkins
echo ""
echo "🔧 Installing Jenkins..."

# Add Jenkins repository key
curl -fsSL https://pkg.jenkins.io/debian-stable/jenkins.io-2023.key | tee \
  /usr/share/keyrings/jenkins-keyring.asc > /dev/null

# Add Jenkins repository
echo deb [signed-by=/usr/share/keyrings/jenkins-keyring.asc] \
  https://pkg.jenkins.io/debian-stable binary/ | tee \
  /etc/apt/sources.list.d/jenkins.list > /dev/null

# Update package list and install Jenkins
apt update
apt install -y jenkins

# Start Jenkins
systemctl start jenkins
systemctl enable jenkins

echo "✅ Jenkins installed successfully"

# Install Docker
echo ""
echo "🐳 Installing Docker..."
apt install -y docker.io

# Start Docker
systemctl start docker
systemctl enable docker

echo "✅ Docker installed successfully"

# Add Jenkins user to Docker group
echo ""
echo "👤 Adding Jenkins user to Docker group..."
usermod -aG docker jenkins

# Install Git
echo ""
echo "📚 Installing Git..."
apt install -y git

echo "✅ Git installed successfully"

# Install curl (if not already installed)
apt install -y curl

# Restart Jenkins to apply group changes
echo ""
echo "🔄 Restarting Jenkins..."
systemctl restart jenkins

# Wait for Jenkins to start
echo ""
echo "⏳ Waiting for Jenkins to start (30 seconds)..."
sleep 30

# Get Jenkins initial admin password
echo ""
echo "============================================================================"
echo "✅ Installation Complete!"
echo "============================================================================"
echo ""
echo "📋 Next Steps:"
echo ""
echo "1. Access Jenkins at: http://$(hostname -I | awk '{print $1}'):8080"
echo ""
echo "2. Use this initial admin password:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
cat /var/lib/jenkins/secrets/initialAdminPassword
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "3. Install suggested plugins"
echo "4. Create your first admin user"
echo "5. Follow the JENKINS_DEPLOYMENT.md guide for complete setup"
echo ""
echo "============================================================================"
echo "📊 Installed Versions:"
echo "============================================================================"
echo -n "Java: "
java -version 2>&1 | head -n 1
echo -n "Jenkins: "
jenkins --version 2>/dev/null || echo "Check at http://localhost:8080"
echo -n "Docker: "
docker --version
echo -n "Git: "
git --version
echo ""
echo "============================================================================"
echo "🎉 Happy Deploying!"
echo "============================================================================"
