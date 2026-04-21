# Naukari Profile Auto-Updater

Automated script to update your Naukari.com profile daily at 10:30 AM, maintaining profile freshness by toggling the full stop at the end of your profile description.

## ✨ Features

- ✅ **Automated Login**: Secure login to Naukari.com
- ✅ **Profile Update**: Automatically checks and updates profile punctuation
- ✅ **Scheduled Execution**: Runs daily at 10:30 AM
- ✅ **GCP Ready**: Deploy on GCP Compute Engine (free tier)
- ✅ **Comprehensive Logging**: Detailed logs and execution history
- ✅ **Error Handling**: Robust error handling and retries
- ✅ **Production Ready**: Security best practices, configuration management
- ✅ **Debug Mode**: Screenshots and detailed logging for troubleshooting

## 📋 Prerequisites

- Python 3.8+
- GCP Account (free tier sufficient)
- Naukari.com username and password
- Git (for version control)

## 🚀 Quick Start (Local)

### 1. Clone Repository
```bash
git clone <repository-url>
cd naukari-profile-updater
```

### 2. Create Virtual Environment
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
playwright install chromium
```

### 4. Configure Credentials

#### Option A: Using .env file
```bash
cp config/.env.example config/.env

# Edit config/.env with your Naukari credentials
# NAUKARI_EMAIL=your_email@example.com
# NAUKARI_PASSWORD=your_password
```

#### Option B: Using config.json
```bash
cp config/config.json.example config/config.json

# Edit config/config.json with your credentials
```

#### Option C: Environment Variables
```bash
export NAUKARI_EMAIL="your_email@example.com"
export NAUKARI_PASSWORD="your_password"
```

### 5. Test Locally
```bash
# Run once
python src/naukari_automator.py

# Run with debug mode (screenshots saved)
DEBUG=true python src/naukari_automator.py
```

### 6. Set Up Local Scheduler (Optional)
```bash
python src/scheduler.py
```

## ☁️ GCP Deployment (Free Tier)

### Option 1: Compute Engine (Recommended for Free Tier)

#### Step 1: Create GCP Project
```bash
gcloud projects create naukari-updater --name="Naukari Profile Updater"
gcloud config set project naukari-updater
```

#### Step 2: Create Free Tier VM Instance
```bash
gcloud compute instances create naukari-updater-vm \
  --zone=us-central1-a \
  --machine-type=f1-micro \
  --image-family=ubuntu-2204-lts \
  --image-project=ubuntu-os-cloud \
  --boot-disk-size=30GB \
  --boot-disk-type=pd-standard \
  --scopes=default,compute-rw
```

#### Step 3: SSH into VM
```bash
gcloud compute ssh naukari-updater-vm --zone=us-central1-a
```

#### Step 4: Set Up on VM
```bash
# Update system
sudo apt-get update && sudo apt-get upgrade -y

# Install Python and dependencies
sudo apt-get install -y python3-pip python3-venv git

# Clone repository
git clone <repository-url>
cd naukari-profile-updater

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
playwright install chromium

# Configure credentials (use environment variables recommended for production)
export NAUKARI_EMAIL="your_email@example.com"
export NAUKARI_PASSWORD="your_password"
```

#### Step 5: Set Up Cron Job
```bash
# Open crontab editor
crontab -e

# Add this line to run at 10:30 AM daily (UTC)
30 10 * * * cd /path/to/naukari-profile-updater && /path/to/venv/bin/python src/naukari_automator.py >> /path/to/logs/cron.log 2>&1
```

**Note**: Adjust time zone if needed. For IST (UTC+5:30), use 5:00 (10:30 AM IST = 5:00 AM UTC).

#### Step 6: Verify Setup
```bash
# Check if cron job is set
crontab -l

# View logs
tail -f /path/to/logs/naukari_updater.log
```

### Option 2: Cloud Functions (Serverless)

#### Deploy Cloud Function
```bash
# Create Cloud Function
gcloud functions deploy naukari-updater \
  --runtime python311 \
  --trigger-topic naukari-update-trigger \
  --entry-point main \
  --allow-unauthenticated

# Set up Cloud Scheduler to trigger
gcloud scheduler jobs create pubsub naukari-profile-update \
  --schedule="30 10 * * *" \
  --topic=naukari-update-trigger \
  --message-body='{"action": "update_profile"}'
```

### Option 3: Cloud Run (Container-based)

See `deployment/gcp-cloud-run.md` for detailed instructions.

## 📂 Project Structure

```
naukari-profile-updater/
├── src/
│   ├── naukari_automator.py      # Main automation script
│   ├── scheduler.py               # Scheduling logic
│   └── __init__.py
├── config/
│   ├── settings.py                # Configuration management
│   ├── config.json.example        # Config template
│   ├── .env.example               # Environment template
│   └── __init__.py
├── tests/
│   ├── test_automator.py          # Unit tests
│   └── __init__.py
├── deployment/
│   ├── gcp-compute-engine.md      # Compute Engine guide
│   ├── gcp-cloud-functions.md     # Cloud Functions guide
│   ├── gcp-cloud-run.md           # Cloud Run guide
│   └── startup-script.sh           # GCP startup script
├── logs/                          # Execution logs (auto-created)
├── requirements.txt               # Python dependencies
├── README.md                      # This file
├── LICENSE                        # MIT License
├── .gitignore                     # Git ignore rules
└── .github/
    └── workflows/                 # GitHub Actions (CI/CD)
```

## 🔐 Security Considerations

- **Never commit credentials**: Use `.env` or environment variables
- **Rotate passwords**: Update credentials periodically
- **Use secrets manager**: On GCP, use Secret Manager for production
- **Enable 2FA carefully**: If Naukari supports it, test with 2FA enabled
- **Audit logs**: Regularly review `logs/naukari_updater.log`

### Using GCP Secret Manager (Recommended)

```bash
# Create secret
echo -n "your_password" | gcloud secrets create naukari-password --data-file=-

# Grant access to service account
gcloud secrets add-iam-policy-binding naukari-password \
  --member=serviceAccount:your-sa@PROJECT.iam.gserviceaccount.com \
  --role=roles/secretmanager.secretAccessor

# Access in code
from google.cloud import secretmanager
client = secretmanager.SecretManagerServiceClient()
secret = client.access_secret_version(request={"name": "projects/PROJECT/secrets/naukari-password/versions/latest"})
password = secret.payload.data.decode("UTF-8")
```

## 📊 Logging and Monitoring

### Local Logs
```
logs/
├── naukari_updater.log          # Main application log
├── execution_history.json        # Execution records
└── screenshots/                  # Debug screenshots (if enabled)
```

### GCP Monitoring
```bash
# View logs
gcloud logging read "resource.type=gce_instance AND jsonPayload.application=naukari-updater" --limit 50

# Set up alerts (optional)
gcloud alpha monitoring policies create \
  --notification-channels=CHANNEL_ID \
  --alert-strategy=auto-close=1800s
```

## 🧪 Testing

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest tests/ --cov=src --cov-report=html

# Test specific module
pytest tests/test_automator.py -v
```

## 🔧 Troubleshooting

### Login Fails
- Verify credentials in `.env` or environment variables
- Check if Naukari requires 2FA
- Review screenshots in `logs/` (if debug=true)

### Profile Not Found
- Ensure you're logged in successfully
- Check if profile page URL has changed
- Enable debug mode: `DEBUG=true python src/naukari_automator.py`

### Cron Job Not Running
```bash
# Check cron service
sudo service cron status

# Check system logs
sudo tail -f /var/log/syslog | grep CRON

# Verify cron is set
crontab -l

# Test cron manually
/path/to/venv/bin/python /path/to/naukari_automator.py
```

### GCP VM Issues
```bash
# Check VM status
gcloud compute instances describe naukari-updater-vm --zone=us-central1-a

# Check VM logs
gcloud compute instances get-serial-port-output naukari-updater-vm --zone=us-central1-a

# SSH into VM for debugging
gcloud compute ssh naukari-updater-vm --zone=us-central1-a
```

## 📈 Performance & Cost

### GCP Free Tier Limits (as of 2024)
- **Compute Engine**: 1 f1-micro instance per month (continuous)
- **Cloud Storage**: 5GB free storage
- **Cloud Logging**: 50GB logs per month
- **Cloud Scheduler**: 3 free jobs per month

### Estimated Monthly Cost (if exceeding free tier)
- f1-micro: ~$6/month
- Data egress: ~$0.12/GB
- **Total with free tier**: $0/month

## 🚦 Status Indicators

- ✅ **Green**: Profile updated successfully
- ⚠️ **Yellow**: Update completed with warnings
- ❌ **Red**: Update failed, check logs

## 📝 Logging Format

```
2024-01-15 10:30:45,123 - INFO - Starting Naukari Profile Auto-Updater
2024-01-15 10:30:46,456 - INFO - Browser started successfully
2024-01-15 10:30:52,789 - INFO - Login successful
2024-01-15 10:31:05,012 - INFO - Profile updated successfully
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests: `pytest`
5. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details

## ⚠️ Disclaimer

- **Use at your own risk**: This tool automates interactions with Naukari.com
- **Terms of Service**: Ensure this complies with Naukari's Terms of Service
- **Rate Limiting**: Naukari may rate-limit automated requests
- **Account Risk**: Use at your own risk - account suspension may occur if detected

## 🎯 Future Enhancements

- [ ] Add support for updating other profile fields
- [ ] Multi-account support
- [ ] Email notifications
- [ ] Web dashboard for monitoring
- [ ] Mobile app integration
- [ ] AI-powered profile optimization

## 📞 Support

For issues, questions, or contributions:
1. Check existing issues on GitHub
2. Review logs in `logs/` directory
3. Create detailed issue with screenshots

## 🔗 Useful Links

- [Naukari.com](https://www.naukari.com)
- [Playwright Documentation](https://playwright.dev)
- [GCP Free Tier](https://cloud.google.com/free)
- [Python Schedule Library](https://schedule.readthedocs.io)

---

**Last Updated**: 2024-01-15  
**Version**: 1.0.0  
**Status**: ✅ Production Ready
