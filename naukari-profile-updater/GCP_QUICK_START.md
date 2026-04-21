# GCP Setup Guide (30-Minute Quick Start)

Quick reference for deploying on GCP Free Tier.

## 🎯 **Option 1: Compute Engine (Recommended for Free Tier)**

### Prerequisites (5 minutes)
```bash
# Install gcloud CLI
# Windows: https://cloud.google.com/sdk/docs/install#windows
# macOS: brew install google-cloud-sdk
# Linux: https://cloud.google.com/sdk/docs/install#linux

gcloud init
gcloud auth login
```

### Setup (25 minutes)

```bash
# 1. Create project (2 min)
PROJECT_ID="naukari-updater-$(date +%s)"
gcloud projects create $PROJECT_ID --name="Naukari Profile Updater"
gcloud config set project $PROJECT_ID

# 2. Enable APIs (1 min)
gcloud services enable compute.googleapis.com logging.googleapis.com

# 3. Create VM instance (3 min)
gcloud compute instances create naukari-vm \
  --zone=us-central1-a \
  --machine-type=f1-micro \
  --image-family=ubuntu-2204-lts \
  --image-project=ubuntu-os-cloud

# 4. SSH into VM (1 min)
gcloud compute ssh naukari-vm --zone=us-central1-a

# On the VM, run these commands:
# 5. Setup on VM (18 min total)
sudo apt-get update && sudo apt-get upgrade -y
sudo apt-get install -y python3-pip python3-venv git chromium-browser

mkdir -p /opt/naukari-updater && cd /opt/naukari-updater
git clone https://github.com/YOUR_USERNAME/naukari-profile-updater.git .

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
playwright install chromium

# 6. Configure credentials (2 min)
sudo nano .env.production
# Add:
# NAUKARI_EMAIL=your_email@example.com
# NAUKARI_PASSWORD=your_password
# DEBUG=false
# HEADLESS=true

# 7. Test (1 min)
export $(cat .env.production | grep -v '^#' | xargs)
python src/naukari_automator.py

# 8. Setup cron (2 min)
sudo crontab -e
# Add this line:
# 30 10 * * * cd /opt/naukari-updater && source venv/bin/activate && export $(cat .env.production | grep -v '^#' | xargs) && python src/naukari_automator.py >> /var/log/naukari.log 2>&1

# 9. Verify cron
sudo crontab -l
```

## 📊 **Option 2: Cloud Scheduler + Cloud Functions (Serverless)**

```bash
# Enable services
gcloud services enable cloudfunctions.googleapis.com cloudscheduler.googleapis.com

# Create Cloud Function trigger (via UI or CLI)
# Then set scheduler job

# Or via CLI:
gcloud scheduler jobs create pubsub naukari-update \
  --schedule="30 10 * * *" \
  --topic=naukari-trigger \
  --message-body='{}'
```

## ✅ Verify Installation

```bash
# Check VM is running
gcloud compute instances list

# SSH and check logs
gcloud compute ssh naukari-vm --zone=us-central1-a
tail -f /var/log/naukari.log

# Manually trigger to test
cd /opt/naukari-updater
source venv/bin/activate
export $(cat .env.production | grep -v '^#' | xargs)
python src/naukari_automator.py
```

## 💰 **Monitor Costs**

```bash
# Set budget alert
gcloud billing budgets create \
  --billing-account=YOUR_ACCOUNT_ID \
  --display-name="Naukari Budget" \
  --budget-amount=5
```

## 🧹 **Cleanup**

```bash
# Delete VM
gcloud compute instances delete naukari-vm --zone=us-central1-a

# Delete project
gcloud projects delete $PROJECT_ID
```

## 🔐 **Security - Use Secret Manager (Advanced)**

```bash
# Store password securely
echo -n "your_password" | gcloud secrets create naukari-password --data-file=-

# Update code to fetch from Secret Manager
# (See src/naukari_automator.py for integration example)
```

## 📝 **Timezone Notes**

- **VM Timezone**: Default is UTC
- **For IST (UTC+5:30)**: Adjust cron time from 10:30 to 5:00 (10:30 IST = 5:00 UTC)
- **Or set timezone**: `sudo timedatectl set-timezone Asia/Kolkata`

## 🆘 **Troubleshooting**

```bash
# Cron not running?
sudo service cron restart
sudo grep CRON /var/log/syslog | tail -10

# Check application logs
tail -f /var/log/naukari.log

# Test manually
/opt/naukari-updater/venv/bin/python /opt/naukari-updater/src/naukari_automator.py

# Memory/CPU usage
free -h
top

# Check if chromium is installed
which chromium-browser
```

## 📞 **Support Resources**

- [GCP Free Tier Info](https://cloud.google.com/free)
- [gcloud CLI Reference](https://cloud.google.com/sdk/gcloud)
- [Compute Engine Docs](https://cloud.google.com/compute/docs)
- [Cloud Scheduler Docs](https://cloud.google.com/scheduler/docs)

---

**Estimated Time**: 30 minutes  
**Estimated Cost**: $0 (free tier)  
**Status**: ✅ Production Ready
