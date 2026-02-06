# 🔑 API Keys Guide - AI Voice Detection System

This guide explains all the API keys you need for the AI Voice Detection project, where to get them, and how to configure them.

---

## 📋 Overview: What API Keys Do You Need?

| API Key | Required? | Purpose | Where to Get |
|---------|-----------|---------|--------------|
| **Voice Detection API Key** | ✅ Yes | Authenticate requests to YOUR API | Self-generated (see below) |
| **Sentry DSN** | ❌ Optional | Error tracking & monitoring | [sentry.io](https://sentry.io) |
| **Cloud Provider Keys** | ❌ Optional | Deploy to cloud (AWS/GCP/Azure) | Cloud provider console |

---

## 1️⃣ Voice Detection API Key (REQUIRED)

### What Is It?
This is the API key that **YOUR users** will use to access your Voice Detection API. You create and manage these keys yourself - no external service needed!

### How It Works
```
User → Sends request with X-API-Key header → Your API validates → Returns result
```

### Step-by-Step: Generate Your Own API Keys

#### Option A: Using Python (Recommended)

```python
import secrets

# Generate a secure 32-byte API key
api_key = secrets.token_urlsafe(32)
print(f"Your new API key: {api_key}")

# Example output: "xK7mN2pQ9rS5tU8vW3xY6zA4bC1dE7fG9hI2jK5lM8n"
```

#### Option B: Using PowerShell (Windows)

```powershell
# Generate a random API key
[Convert]::ToBase64String([Security.Cryptography.RandomNumberGenerator]::GetBytes(32))
```

#### Option C: Using Command Line

```bash
# Linux/Mac
openssl rand -base64 32

# Or using Python one-liner
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### Configure Your API Keys

**Step 1:** Generate your API keys (use the Python method above)

**Step 2:** Add them to your `.env` file:
```bash
# .env file
API_KEYS=your_first_key_here,your_second_key_here,demo_key_12345
```

**Step 3:** Or set in `app/config.py`:
```python
api_keys: Set[str] = {"demo_key_12345", "your_production_key_here"}
```

### Default Demo Key
For testing, we've included a demo key:
```
demo_key_12345
```

⚠️ **WARNING**: Replace this with secure keys in production!

---

## 2️⃣ Sentry DSN (OPTIONAL - Error Tracking)

### What Is It?
Sentry is an error tracking service that captures and alerts you about errors in your API.

### Do You Need It?
- **Development**: ❌ No - skip this
- **Production**: ✅ Recommended for monitoring errors

### Step-by-Step: Get Sentry DSN

**Step 1:** Go to [https://sentry.io](https://sentry.io)

**Step 2:** Click "Start for Free" or "Sign Up"

**Step 3:** Create an account (you can use GitHub/Google login)

**Step 4:** Create a new project:
- Select platform: **Python**
- Choose framework: **FastAPI**
- Name your project: `voice-detection-api`

**Step 5:** Copy your DSN (it looks like this):
```
https://abc123def456@o123456.ingest.sentry.io/789012
```

**Step 6:** Add to your `.env` file:
```bash
SENTRY_DSN=https://abc123def456@o123456.ingest.sentry.io/789012
```

### Sentry Pricing
| Plan | Price | Requests/Month |
|------|-------|----------------|
| Developer | **FREE** | 5,000 errors |
| Team | $26/mo | 50,000 errors |
| Business | $80/mo | 100,000 errors |

👉 **Recommendation**: Start with FREE plan - it's enough for most projects!

---

## 3️⃣ Cloud Provider Keys (OPTIONAL - Deployment)

Only needed if you want to deploy to cloud services.

### AWS (Amazon Web Services)

**Step 1:** Go to [https://aws.amazon.com](https://aws.amazon.com)

**Step 2:** Create an account (requires credit card)

**Step 3:** Go to IAM Console → Users → Add User

**Step 4:** Create access keys:
- User name: `voice-detection-deployer`
- Access type: Programmatic access
- Permissions: Attach `AmazonEC2ContainerRegistryFullAccess`, `AmazonECS_FullAccess`

**Step 5:** Save your credentials:
```bash
AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
AWS_REGION=us-east-1
```

### Google Cloud Platform (GCP)

**Step 1:** Go to [https://cloud.google.com](https://cloud.google.com)

**Step 2:** Create a project

**Step 3:** Go to IAM & Admin → Service Accounts

**Step 4:** Create service account:
- Name: `voice-detection-deployer`
- Role: Cloud Run Admin, Container Registry access

**Step 5:** Create JSON key and download

**Step 6:** Set environment variable:
```bash
GOOGLE_APPLICATION_CREDENTIALS=/path/to/your-key.json
```

### Microsoft Azure

**Step 1:** Go to [https://portal.azure.com](https://portal.azure.com)

**Step 2:** Create Azure account

**Step 3:** Go to Azure Active Directory → App Registrations

**Step 4:** Create new registration and note:
```bash
AZURE_CLIENT_ID=your-client-id
AZURE_CLIENT_SECRET=your-client-secret
AZURE_TENANT_ID=your-tenant-id
AZURE_SUBSCRIPTION_ID=your-subscription-id
```

---

## 4️⃣ Database Credentials (OPTIONAL)

For PostgreSQL database (only if using Docker Compose with database logging):

### Default Development Credentials
Already configured in `docker-compose.yml`:
```bash
POSTGRES_DB=voicedb
POSTGRES_USER=voiceuser
POSTGRES_PASSWORD=voicepass
```

⚠️ **For Production**: Change these passwords!

### Generate Secure Database Password
```python
import secrets
password = secrets.token_urlsafe(24)
print(f"Database password: {password}")
```

---

## 5️⃣ Redis Credentials (OPTIONAL)

For caching (only if using Redis):

### Default (No Password)
Redis in Docker Compose runs without password by default.

### Add Password for Production
```bash
# In docker-compose.yml, modify redis command:
command: redis-server --requirepass your_redis_password

# In .env:
REDIS_URL=redis://:your_redis_password@redis:6379
```

---

## 📝 Complete .env Example

Here's a complete `.env` file with all possible keys:

```bash
# ========================================
# AI VOICE DETECTION API - CONFIGURATION
# ========================================

# === REQUIRED ===
# Your API keys (comma-separated)
# Generate with: python -c "import secrets; print(secrets.token_urlsafe(32))"
API_KEYS=demo_key_12345,your_production_key_here

# === OPTIONAL: Error Tracking ===
# Get from: https://sentry.io (free tier available)
# SENTRY_DSN=https://abc123@o123456.ingest.sentry.io/789012

# === OPTIONAL: Database ===
# DATABASE_URL=postgresql://voiceuser:voicepass@localhost:5432/voicedb

# === OPTIONAL: Redis Cache ===
# REDIS_URL=redis://localhost:6379

# === OPTIONAL: Cloud Deployment ===
# AWS
# AWS_ACCESS_KEY_ID=your_aws_key
# AWS_SECRET_ACCESS_KEY=your_aws_secret
# AWS_REGION=us-east-1

# GCP
# GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json

# Azure
# AZURE_CLIENT_ID=your_client_id
# AZURE_CLIENT_SECRET=your_client_secret
```

---

## ✅ Quick Checklist

### For Development (Minimum Required)
- [x] Use default `demo_key_12345` - **Already configured!**
- [ ] No other keys needed for local development

### For Production
- [ ] Generate secure API keys (replace demo key)
- [ ] Set up Sentry for error tracking (recommended)
- [ ] Configure cloud provider credentials (for deployment)
- [ ] Change default database passwords

---

## 🔐 Security Best Practices

1. **Never commit API keys to Git**
   ```bash
   # Add to .gitignore
   .env
   *.pem
   *-key.json
   ```

2. **Use environment variables, not hardcoded values**

3. **Rotate keys regularly** (every 90 days recommended)

4. **Use different keys for dev/staging/production**

5. **Limit key permissions** to only what's needed

---

## 🆘 Need Help?

### Generate a Quick API Key Right Now
```python
# Run this in Python
import secrets
print(f"Your API Key: {secrets.token_urlsafe(32)}")
```

### Test Your API Key
```bash
# PowerShell
$headers = @{"X-API-Key"="your_key_here"}
Invoke-RestMethod -Uri "http://localhost:8000/health"

# The /health endpoint works without a key
# The /detect endpoint requires a valid key
```

---

## 📞 Summary

| What You Need | For Development | For Production |
|---------------|-----------------|----------------|
| Voice Detection API Key | Use `demo_key_12345` | Generate secure key |
| Sentry DSN | Skip | Get from sentry.io (free) |
| Cloud Keys | Skip | Get from AWS/GCP/Azure |
| Database Password | Use defaults | Generate secure password |

**Bottom Line**: For local development, you don't need ANY external API keys! Just use the included `demo_key_12345`. 🎉

---

**Created for AI Voice Detection System v1.0.0**
