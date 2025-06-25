# SECURITY ALERT: API Key Remediation Steps

## 🚨 IMMEDIATE ACTIONS REQUIRED

### 1. Revoke the Exposed Google API Key
- Go to Google Cloud Console: https://console.cloud.google.com/apis/credentials
- Find API Key: `AIzaSyBMPftvY3Y3ern0fzfF_6Bww6AoJVgLsUo`
- **DELETE or REVOKE this key immediately**

### 2. Create a New Google API Key
1. Go to Google Cloud Console > APIs & Services > Credentials
2. Click "Create Credentials" > "API Key"
3. Copy the new API key
4. Restrict the key to only necessary APIs:
   - Generative Language API
   - Fact Check Tools API (if needed)

### 3. Update Local Environment
```bash
# Update your local .env file with the new key
GOOGLE_API_KEY=your_new_google_api_key_here
```

### 4. Update Cloud Run Service
```bash
# Update the service with new API key
gcloud run services update factos-agents \
  --region=us-central1 \
  --set-env-vars="GOOGLE_API_KEY=your_new_api_key_here"
```

### 5. Security Review
- [ ] Check Google Cloud Audit Logs for unauthorized usage
- [ ] Review all commits that might have exposed the key
- [ ] Verify .env is in .gitignore (✅ Already done)
- [ ] Ensure .env.example has no real keys (✅ Already done)

### 6. Files That Contained Exposed Keys
- `/Users/gibrann/Documents/factos_agents/.env` (✅ FIXED)
- Cloud Run service environment variables (❌ NEEDS UPDATE)

### 7. GitHub Repository Security
- Check if repository is public and contains exposed keys
- Remove any commits with exposed keys from git history if needed

## NEXT STEPS:
1. **IMMEDIATELY** revoke the old key in Google Cloud Console
2. Create new API key with proper restrictions
3. Test locally with new key
4. Update Cloud Run service
5. Close GitHub security alert as "revoked"
