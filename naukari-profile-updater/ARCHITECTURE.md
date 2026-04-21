# Architecture and Design Document

## Overview

The Naukari Profile Auto-Updater is an automated system designed to keep your Naukari.com profile fresh by toggling punctuation daily. It combines web automation, scheduling, and cloud deployment for a complete solution.

## System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    GCP DEPLOYMENT                       │
│                                                         │
│  ┌────────────────────────────────────────────────────┐ │
│  │     Compute Engine (f1-micro)                      │ │
│  │                                                    │ │
│  │  ┌─────────────────────────────────────────────┐  │ │
│  │  │  Cron Job (10:30 AM UTC)                   │  │ │
│  │  │  Runs: python naukari_automator.py         │  │ │
│  │  └─────────────────────────────────────────────┘  │ │
│  │                      │                            │ │
│  │                      ▼                            │ │
│  │  ┌─────────────────────────────────────────────┐  │ │
│  │  │  Naukari Automator                         │  │ │
│  │  │  ├─ Login Handler                          │  │ │
│  │  │  ├─ Profile Navigator                      │  │ │
│  │  │  ├─ Text Processor                         │  │ │
│  │  │  └─ Saver Handler                          │  │ │
│  │  └─────────────────────────────────────────────┘  │ │
│  │                      │                            │ │
│  │                      ▼                            │ │
│  │  ┌─────────────────────────────────────────────┐  │ │
│  │  │  Playwright (Headless Browser)             │  │ │
│  │  │  ├─ Navigate                               │  │ │
│  │  │  ├─ Interact                               │  │ │
│  │  │  └─ Extract                                │  │ │
│  │  └─────────────────────────────────────────────┘  │ │
│  │                      │                            │ │
│  │                      ▼                            │ │
│  │  ┌─────────────────────────────────────────────┐  │ │
│  │  │  Naukari.com Website                       │  │ │
│  │  │  ├─ Login Page                             │  │ │
│  │  │  ├─ Profile Page                           │  │ │
│  │  │  └─ Save Function                          │  │ │
│  │  └─────────────────────────────────────────────┘  │ │
│  │                                                    │ │
│  │  ┌─────────────────────────────────────────────┐  │ │
│  │  │  Logging & Monitoring                      │  │ │
│  │  │  ├─ Local Logs (naukari_updater.log)       │  │ │
│  │  │  ├─ Execution History (JSON)               │  │ │
│  │  │  └─ Cloud Logging (optional)               │  │ │
│  │  └─────────────────────────────────────────────┘  │ │
│  └────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

## Component Breakdown

### 1. **NaukariAutomator** (src/naukari_automator.py)
**Purpose**: Core automation engine  
**Responsibilities**:
- Manage Playwright browser lifecycle
- Authenticate with Naukari
- Navigate to profile
- Check and update profile text
- Handle errors and retries
- Generate execution logs

**Key Methods**:
```python
.start()                    # Initialize browser
.login()                    # Authenticate
.navigate_to_profile()      # Go to profile page
.check_and_update_profile() # Main logic
.save_profile()             # Persist changes
.run()                      # Execute full workflow
```

### 2. **Configuration Management** (config/settings.py)
**Purpose**: Handle credentials and settings  
**Features**:
- Load from environment variables (production)
- Load from .env file (development)
- Load from config.json (alternative)
- Validate credentials
- Provide defaults

**Priority Order**:
1. Environment variables
2. .env file
3. config.json
4. Defaults

### 3. **Scheduler** (src/scheduler.py)
**Purpose**: Handle daily execution  
**Options**:
- **LocalScheduler**: Uses Python `schedule` library
- **GCPCloudScheduler**: Integration with GCP Cloud Scheduler
- **Cron**: Native system cron (production on GCP)

### 4. **Logging System**
**Components**:
- File logging: `logs/naukari_updater.log`
- Console output: Real-time feedback
- Execution history: `logs/execution_history.json`
- Debug screenshots: `logs/*.png` (when debug=true)

**Log Levels**:
- DEBUG: Detailed execution traces
- INFO: Normal operation
- WARNING: Non-critical issues
- ERROR: Failed operations

## Execution Flow

```
START
  ├─→ Load Configuration
  │   ├─ Get Credentials
  │   └─ Load Settings
  │
  ├─→ Initialize Browser
  │   └─ Launch Playwright/Chromium
  │
  ├─→ Login to Naukari
  │   ├─ Navigate to login page
  │   ├─ Fill credentials
  │   └─ Submit form
  │
  ├─→ Navigate to Profile
  │   └─ Go to view profile page
  │
  ├─→ Check & Update Profile
  │   ├─ Read current profile text
  │   ├─ Check for full stop
  │   │  ├─ If exists: remove it
  │   │  └─ If missing: add it
  │   └─ Save changes
  │
  ├─→ Save Profile
  │   └─ Click save button
  │
  ├─→ Log Results
  │   ├─ Write to file
  │   └─ Save execution history
  │
  └─→ Cleanup & Exit
      └─ Close browser
```

## Data Flow

```
Naukari.com
    │
    ▲
    │ Login Request
    │ Profile Query
    │ Update Data
    │
┌───┴─────────────────────┐
│  Playwright Browser     │
│  (Headless Chromium)    │
└───┬─────────────────────┘
    │
    │ Browser Control
    │
┌───┴──────────────────────────┐
│  NaukariAutomator            │
│  (Main Logic)                │
└───┬──────────────────────────┘
    │
    │ Credentials │ Config │ Logs
    │
┌───┴──────────┬─────────┬───────┐
│              │         │       │
▼              ▼         ▼       ▼
Settings   Cron/Cloud  Logs    Monitoring
         Scheduler
```

## Error Handling Strategy

```
Try Operation
    │
    ├─→ Success? → Log & Continue
    │
    └─→ Failure?
        │
        ├─→ Timeout? → Retry once
        │   ├─→ Success? → Log & Continue
        │   └─→ Failed? → Log Error & Exit
        │
        ├─→ Network Error? → Log & Exit
        │
        ├─→ Selector Not Found? → Log & Exit
        │   (May indicate page structure changed)
        │
        └─→ Other Error? → Log Stack Trace & Exit
```

## Deployment Options

### 1. **Local Machine**
- Uses local scheduler
- Manual trigger: `python src/naukari_automator.py`
- Always running for scheduled jobs

### 2. **GCP Compute Engine (Recommended)**
- f1-micro instance (free tier)
- Uses system cron for scheduling
- 730 hours/month free
- Zero cost for this use case

### 3. **GCP Cloud Functions**
- Event-triggered execution
- Pay per invocation
- Easier deployment
- May incur costs

### 4. **GCP Cloud Run**
- Containerized deployment
- On-demand execution
- More costly than Compute Engine

## Security Model

### Credential Management
```
Credentials
    │
    ├─→ Option 1: Environment Variables (Recommended)
    │   └─ Set via GCP Secret Manager or VM env
    │
    ├─→ Option 2: .env File
    │   └─ Local development only (git ignored)
    │
    └─→ Option 3: config.json
        └─ Alternative config file (git ignored)
```

### Access Control
- Single user account (your Naukari profile)
- No sharing of credentials
- Secure storage on GCP VM
- Limited to scheduled execution times

### Best Practices
1. Never commit credentials to Git
2. Rotate passwords periodically
3. Use GCP Secret Manager for production
4. Audit logs regularly
5. Restrict SSH access to your IP

## Monitoring & Observability

### Metrics Tracked
- Execution timestamp
- Success/failure status
- Duration in seconds
- Number of updates made
- Error messages (if any)

### Logging
```
/var/log/naukari_updater.log
├─ Timestamp: When execution happened
├─ Log Level: INFO/WARNING/ERROR
├─ Message: What happened
└─ Stack Trace: If error occurred

logs/execution_history.json
└─ Last 100 executions with results
```

### Alerts (Optional)
- Email notification on failure
- Slack webhook integration
- GCP Cloud Monitoring alerts

## Performance Characteristics

### Timing
- Browser startup: ~3-5 seconds
- Login process: ~5-10 seconds
- Profile navigation: ~2-3 seconds
- Text processing: ~1 second
- Save operation: ~1-2 seconds
- **Total**: ~12-21 seconds per execution

### Resource Usage
- Memory: ~200-300 MB (Chromium + Python)
- CPU: Spiky during execution, idle otherwise
- Disk: ~50 MB for dependencies
- Network: Minimal (just Naukari traffic)

### Scalability
- Single profile: Fully supported
- Multiple profiles: Possible with separate VMs/crons
- Load: Negligible on GCP infrastructure

## Future Enhancements

1. **Multi-Profile Support**: Multiple accounts
2. **Notifications**: Email/SMS on success/failure
3. **Analytics Dashboard**: Web UI for monitoring
4. **Profile Optimization**: AI-powered suggestions
5. **Database Logging**: Persistent storage of all executions
6. **Advanced Scheduling**: Different times for different profiles
7. **Retry Logic**: Automatic retries on failure
8. **Webhook Integration**: Trigger from external services

## Technology Stack

- **Language**: Python 3.8+
- **Web Automation**: Playwright
- **Scheduling**: Python `schedule` library / System cron / GCP Cloud Scheduler
- **Cloud Platform**: Google Cloud Platform
- **Logging**: Python logging + JSON
- **Testing**: pytest
- **CI/CD**: GitHub Actions
- **Version Control**: Git / GitHub

## Compliance & Terms

- Compliant with Python best practices
- Follows PEP 8 style guidelines
- MIT Licensed
- No warranty - use at your own risk
- Complies with Naukari Terms of Service*

*Users should verify their own compliance with Naukari.com's Terms of Service.

---

**Document Version**: 1.0  
**Last Updated**: 2024-01-15  
**Status**: ✅ Production Ready
