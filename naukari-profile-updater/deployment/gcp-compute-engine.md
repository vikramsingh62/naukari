# GCP Compute Engine Deployment Guide

Complete guide to deploy Naukari Profile Updater on GCP Compute Engine (Free Tier).

## 🎯 Architecture

```
GCP Compute Engine (f1-micro)
    ├── Cron Job (10:30 AM UTC)
    ├── Python Script
    ├── Playwright Browser
    └── Logs & Monitoring
```

## 📋 Prerequisites

- GCP Account (free tier)
- Git CLI
- gcloud SDK installed locally
- Basic Linux/SSH knowledge

## 🚀 Step-by-Step Deployment

### Step 1: Create GCP Project

```bash
# Set your project details
PROJECT_ID="naukari-updater-$(date +%s)"
PROJECT_NAME="Naukari Profile Updater"
REGION="us-central1"
ZONE="us-central1-a"

# Create project
gcloud projects create $PROJECT_ID --name=$PROJECT_NAME

# Set as default
gcloud config set project $PROJECT_ID

# Enable required APIs
gcloud services enable compute.googleapis.com
gcloud services enable logging.googleapis.com
```

### Step 2: Create Compute Engine Instance

```bash
# Create f1-micro instance (free tier eligible)
gcloud compute instances create naukari-updater \
  --zone=$ZONE \
  --machine-type=f1-micro \
  --image-family=ubuntu-2204-lts \
  --image-project=ubuntu-os-cloud \
  --boot-disk-size=30GB \
  --boot-disk-type=pd-standard \
  --scopes=default,compute-rw,logging-write \
  --metadata=startup-script-url=gs://your-bucket/startup-script.sh

# Or use startup script (see below)
gcloud compute instances create naukari-updater \
  --zone=$ZONE \
  --machine-type=f1-micro \
  --image-family=ubuntu-2204-lts \
  --image-project=ubuntu-os-cloud \
  --boot-disk-size=30GB \
  --boot-disk-type=pd-standard \
  --metadata startup-script='#!/bin/bash
sudo apt-get update
sudo apt-get install -y python3-pip python3-venv git
'
```

### Step 3: SSH into Instance

```bash
# SSH into the instance
gcloud compute ssh naukari-updater --zone=$ZONE

# Or use external IP
gcloud compute instances list
# Then: ssh -i ~/.ssh/google_compute_engine user@EXTERNAL_IP
```

### Step 4: Set Up Application on VM

```bash
# On the VM, run the following commands:

# Update system
sudo apt-get update && sudo apt-get upgrade -y

# Install dependencies
sudo apt-get install -y \
  python3-pip \
  python3-venv \
  git \
  build-essential \
  libssl-dev \
  libffi-dev \
  python3-dev

# Install Chrome/Chromium for Playwright
sudo apt-get install -y chromium-browser

# Create app directory
mkdir -p /opt/naukari-updater
cd /opt/naukari-updater

# Clone repository
git clone https://github.com/yourusername/naukari-profile-updater.git .

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium

# Create logs directory with proper permissions
mkdir -p logs
chmod 755 logs
```

### Step 5: Configure Credentials

#### Option A: Environment Variables (Recommended)

```bash
# Create environment file
sudo nano /opt/naukari-updater/.env.production

# Add your credentials:
NAUKARI_EMAIL=your_email@example.com
NAUKARI_PASSWORD=your_password
DEBUG=false
HEADLESS=true

# Set permissions
sudo chmod 600 /opt/naukari-updater/.env.production
```

#### Option B: Using GCP Secret Manager (More Secure)

```bash
# Create secrets
echo -n "your_password" | gcloud secrets create naukari-password --data-file=-

# Create IAM binding (from local machine)
gcloud secrets add-iam-policy-binding naukari-password \
  --member=serviceAccount:default@$PROJECT_ID.iam.gserviceaccount.com \
  --role=roles/secretmanager.secretAccessor

# Update the Python script to fetch from Secret Manager
# See example below
```

**Update settings.py to fetch from Secret Manager:**

```python
def get_credentials_from_secret_manager():
    """Fetch credentials from GCP Secret Manager"""
    from google.cloud import secretmanager
    
    project_id = os.getenv('GCP_PROJECT_ID')
    
    client = secretmanager.SecretManagerServiceClient()
    
    password_response = client.access_secret_version(
        request={"name": f"projects/{project_id}/secrets/naukari-password/versions/latest"}
    )
    password = password_response.payload.data.decode("UTF-8")
    
    # Email can be from environment variable
    email = os.getenv('NAUKARI_EMAIL')
    
    return email, password
```

### Step 6: Test the Application

```bash
# On the VM, activate venv and test
source /opt/naukari-updater/venv/bin/activate
cd /opt/naukari-updater

# Load environment
export $(cat .env.production | grep -v '^#' | xargs)

# Test run
python src/naukari_automator.py

# Check logs
tail -f logs/naukari_updater.log
```

### Step 7: Set Up Cron Job

```bash
# Edit crontab
sudo crontab -e

# Add this line (runs at 10:30 AM UTC daily)
# For IST (UTC+5:30), adjust to 5:00 AM UTC
30 10 * * * /bin/bash -c 'cd /opt/naukari-updater && source venv/bin/activate && export $(cat .env.production | grep -v "^#" | xargs) && python src/naukari_automator.py' >> /var/log/naukari_updater.log 2>&1

# Verify crontab is set
sudo crontab -l
```

**For IST Timezone:**
```bash
# If your VM is in IST or needs different timezone:
# 10:30 AM IST = 5:00 AM UTC
# So use: 0 5 * * * (for 5:00 AM UTC)

# Check current timezone
timedatectl

# Set timezone if needed
sudo timedatectl set-timezone Asia/Kolkata
# Then use: 30 10 * * * for 10:30 AM IST
```

### Step 8: Set Up Log Forwarding to GCP Logging

```bash
# Install Google Cloud Operations agent
curl https://dl.google.com/cloudagents/add-google-cloud-ops-agent-repo.sh | sudo bash
sudo apt-get update
sudo apt-get install -y google-cloud-ops-agent

# Create configuration
sudo nano /etc/google-cloud-ops-agent/config.yaml

# Add this configuration:
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

# Restart agent
sudo service google-cloud-ops-agent restart
```

### Step 9: Verify Cron Execution

```bash
# Monitor logs in real-time (on VM)
sudo tail -f /var/log/naukari_updater.log

# From local machine, view GCP logs
gcloud logging read "resource.type=gce_instance" --limit 50 --format=json

# Check systemd journal for cron
sudo journalctl -u cron
```

### Step 10: Monitor and Maintain

```bash
# From local machine:

# Check instance status
gcloud compute instances describe naukari-updater --zone=$ZONE

# View serial port output (for debugging)
gcloud compute instances get-serial-port-output naukari-updater --zone=$ZONE

# SSH and check resources
gcloud compute ssh naukari-updater --zone=$ZONE
# Then on VM:
free -h  # Memory usage
df -h    # Disk usage
top      # Running processes
```

## 🔧 Troubleshooting

### Cron Job Not Running

```bash
# Check if cron service is running
sudo service cron status

# Restart cron
sudo service cron restart

# Check for syntax errors in crontab
sudo crontab -e

# View cron logs
sudo grep CRON /var/log/syslog | tail -20
```

### Application Not Starting

```bash
# SSH into VM
gcloud compute ssh naukari-updater --zone=$ZONE

# Check if venv exists
ls -la /opt/naukari-updater/venv

# Test Python
/opt/naukari-updater/venv/bin/python --version

# Test imports
/opt/naukari-updater/venv/bin/python -c "import playwright; print('OK')"

# Run with full error output
/opt/naukari-updater/venv/bin/python /opt/naukari-updater/src/naukari_automator.py
```

### Browser Issues

```bash
# Check if Chromium is installed
which chromium-browser

# Reinstall Playwright browsers
/opt/naukari-updater/venv/bin/playwright install chromium

# Check for missing dependencies
ldd /opt/naukari-updater/venv/lib/python3.x/site-packages/playwright/...
```

### Memory Issues

```bash
# Check memory usage
free -h
vmstat 1 5

# If running out of memory, f1-micro may struggle
# Consider upgrading to e2-micro (if available in free tier)
```

## 📊 Monitoring & Alerts

### Set Up Cloud Logging Sink

```bash
# Create log sink to Cloud Storage for long-term storage
gcloud logging sinks create naukari-logs \
  gs://naukari-logs \
  --log-filter='resource.type="gce_instance" AND logName:"naukari_updater"'
```

### Create Alert Policy

```bash
# Create notification channel first (email)
gcloud alpha monitoring channels create \
  --display-name="Naukari Alert" \
  --type=email \
  --channel-labels=email_address=your_email@example.com

# Create alert for failures (if logs contain "ERROR")
gcloud alpha monitoring policies create \
  --notification-channels=YOUR_CHANNEL_ID \
  --alert-strategy='auto-close=1800s' \
  --display-name="Naukari Update Failure"
```

## 💰 Cost Optimization

1. **Use f1-micro**: Always eligible for free tier ($0/month)
2. **Set budget alerts**: 
   ```bash
   gcloud billing budgets create \
     --billing-account=ACCOUNT_ID \
     --display-name="Naukari Budget" \
     --budget-amount=5 \
     --threshold-rule=percent=100
   ```

3. **Clean up logs**: Archive old logs to Cloud Storage

## 🔒 Security Best Practices

1. **Restrict SSH access**:
   ```bash
   gcloud compute firewall-rules create restrict-ssh \
     --allow=tcp:22 \
     --source-ranges=YOUR_IP/32
   ```

2. **Use service accounts**: Create dedicated SA for logging
3. **Rotate credentials**: Update passwords every 90 days
4. **Enable OS Login**: `gcloud compute project-info add-metadata --metadata=enable-oslogin=TRUE`

## 📈 Scaling (If Needed)

For multiple profiles:
1. Create separate VMs or use same VM with different cron times
2. Use Cloud Functions for serverless approach
3. Use Cloud Run for containerized deployment

## 🧹 Cleanup

```bash
# Delete the instance
gcloud compute instances delete naukari-updater --zone=$ZONE

# Delete firewall rules
gcloud compute firewall-rules delete restrict-ssh

# Delete project (if needed)
gcloud projects delete $PROJECT_ID
```

## 📞 Support

For issues:
1. Check VM serial port output
2. Review GCP Logs
3. Check `/var/log/naukari_updater.log` on VM
4. Review logs via: `gcloud logging read --limit 50 --format=json`

---

**Last Updated**: 2024-01-15  
**Tested On**: Ubuntu 22.04 LTS
