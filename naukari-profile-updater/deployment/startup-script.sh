#!/bin/bash

# GCP Compute Engine Startup Script
# Automatically configures the instance for Naukari Profile Updater

set -e

# Logging
exec 1> >(logger -s -t $(basename $0))
exec 2>&1

echo "=========================================="
echo "Starting Naukari Profile Updater Setup"
echo "=========================================="

# Update system
echo "Updating system packages..."
apt-get update
apt-get upgrade -y

# Install dependencies
echo "Installing dependencies..."
apt-get install -y \
    python3-pip \
    python3-venv \
    git \
    build-essential \
    libssl-dev \
    libffi-dev \
    python3-dev \
    chromium-browser \
    curl \
    wget \
    htop

# Create application directory
echo "Creating application directory..."
mkdir -p /opt/naukari-updater
cd /opt/naukari-updater

# Clone repository
echo "Cloning repository..."
git clone https://github.com/YOUR_USERNAME/naukari-profile-updater.git . || true

# Create virtual environment
echo "Setting up Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip setuptools wheel

# Install dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Install Playwright browsers
echo "Installing Playwright browsers..."
playwright install chromium

# Create logs directory
mkdir -p logs
chmod 755 logs

# Create application directories
mkdir -p /var/log/naukari
chmod 755 /var/log/naukari

# Install Google Cloud Operations Agent (for logging)
echo "Installing Google Cloud Operations Agent..."
curl https://dl.google.com/cloudagents/add-google-cloud-ops-agent-repo.sh | bash
apt-get update
apt-get install -y google-cloud-ops-agent

# Create ops agent configuration
echo "Configuring logging..."
cat > /etc/google-cloud-ops-agent/config.yaml <<EOF
logging:
  receivers:
    syslog:
      type: files
      include_paths:
      - /var/log/naukari_updater.log
  exporters:
    google_cloud_logging:
      type: google_cloud_logging
  service:
    pipelines:
      default_pipeline:
        receivers: [syslog]
        exporters: [google_cloud_logging]
EOF

# Restart ops agent
systemctl restart google-cloud-ops-agent

# Create cron job
echo "Setting up cron job..."

# NOTE: Configure your timezone and credentials before production use
# For UTC: run at 10:30 AM UTC
# For IST (UTC+5:30): run at 5:00 AM UTC (5:00 = 10:30 IST)

cat > /etc/cron.d/naukari-updater <<'CRONJOB'
# Run Naukari Profile Updater daily at 10:30 AM UTC
# Change time as needed based on your timezone

30 10 * * * root /bin/bash -c 'cd /opt/naukari-updater && source venv/bin/activate && export $(cat /opt/naukari-updater/.env.production 2>/dev/null | grep -v "^#" | xargs) && python src/naukari_automator.py' >> /var/log/naukari_updater.log 2>&1
CRONJOB

chmod 644 /etc/cron.d/naukari-updater

# Set permissions
chown -R root:root /opt/naukari-updater
chmod 755 /opt/naukari-updater

echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. SSH into the instance"
echo "2. Configure credentials at /opt/naukari-updater/.env.production"
echo "3. Test the application: source /opt/naukari-updater/venv/bin/activate && python /opt/naukari-updater/src/naukari_automator.py"
echo "4. Monitor logs: tail -f /var/log/naukari_updater.log"
echo ""
echo "Cron job will run daily at 10:30 AM UTC"
echo "Adjust cron time in /etc/cron.d/naukari-updater as needed"
echo ""
