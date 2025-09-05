# 🔐 Duotopia Security Best Practices

> **⚠️ CRITICAL**: Database password has been exposed in git history (commit e6f21fe).
> **IMMEDIATE ACTION REQUIRED**: Rotate Supabase password in dashboard!

## 🚨 Security Incident Response

### If Credentials Are Exposed

1. **IMMEDIATELY rotate the exposed credential**
   - Supabase: Dashboard → Settings → Database → Password
   - JWT: Run `./scripts/manage-secrets.sh rotate-jwt`

2. **Update all locations**
   ```bash
   # Local env files
   .env.staging
   backend/.env.staging

   # GitHub Secrets
   https://github.com/Youngger9765/duotopia/settings/secrets/actions
   ```

3. **Verify no active breaches**
   ```bash
   # Check recent database activity
   # Check Cloud Run logs for suspicious access
   gcloud run logs read duotopia-backend --limit=100
   ```

## 🛡️ Security Tools & Checks

### Pre-commit Hooks (Automated)
```bash
# Already configured in .pre-commit-config.yaml
- detect-secrets: Scans for API keys, passwords, tokens
- check-credentials: Prevents hardcoded credentials
- check-database-urls: Blocks exposed database URLs
```

### Manual Security Checks
```bash
# Run comprehensive security check
./scripts/manage-secrets.sh check

# Validate environment files
./scripts/manage-secrets.sh validate

# Check for secrets in git history
git log -p | grep -E "password|secret|key|token" | grep -v "dummy"
```

### GitHub Actions Security Scanning
- **Runs on**: Every push, PR, and daily
- **Includes**:
  - TruffleHog secret scanning
  - CodeQL analysis
  - Dependency vulnerability checks
  - Credential exposure detection

## ✅ Security Checklist

### Environment Variables
- [ ] Never hardcode credentials in code
- [ ] Always use `.env` files for local development
- [ ] Ensure `.env` files are in `.gitignore`
- [ ] Use GitHub Secrets for CI/CD
- [ ] Load credentials from environment variables only

### Database Security
```bash
# ❌ NEVER DO THIS
DATABASE_URL="postgresql://user:password@host/db"  # In code

# ✅ ALWAYS DO THIS
DATABASE_URL = os.getenv("DATABASE_URL")  # Load from environment
```

### Makefile Security
```bash
# ❌ WRONG - Exposes password
DATABASE_URL="postgresql://user:pass@host/db" python script.py

# ✅ CORRECT - Uses environment variable
source .env && DATABASE_URL="$$DATABASE_URL" python script.py
```

### API Keys & Tokens
- Rotate JWT secrets regularly
- Use short expiration times (30 minutes)
- Never log tokens or API keys
- Implement rate limiting

## 🔄 Regular Security Tasks

### Daily
- Monitor GitHub security alerts
- Check Cloud Run logs for anomalies

### Weekly
- Review dependency vulnerabilities
- Run `npm audit` and `pip check`

### Monthly
- Rotate JWT secrets
- Review access logs
- Update dependencies

### On Each Deployment
```bash
# Before deploying
./scripts/manage-secrets.sh check

# After deploying
- Verify health checks
- Check error logs
- Test authentication
```

## 📋 Security Configuration Files

### `.gitignore` (Must Include)
```
.env
.env.*
*.pem
*.key
*.cert
.secrets.baseline
```

### Required GitHub Secrets
```
STAGING_DATABASE_URL
STAGING_JWT_SECRET
STAGING_OPENAI_API_KEY
PRODUCTION_DATABASE_URL
PRODUCTION_JWT_SECRET
PRODUCTION_OPENAI_API_KEY
```

## 🚫 Common Security Mistakes to Avoid

1. **Committing .env files**
   - Even temporarily
   - Even with "dummy" data

2. **Hardcoding credentials "temporarily"**
   - It's never temporary
   - Always ends up in git history

3. **Using production credentials locally**
   - Always use separate dev credentials
   - Never copy production .env locally

4. **Logging sensitive data**
   - Never log passwords, tokens, or API keys
   - Sanitize error messages

5. **Weak JWT secrets**
   - Use cryptographically strong secrets
   - Minimum 32 characters

## 🔧 Security Tools Installation

```bash
# Install pre-commit hooks
pip install pre-commit
pre-commit install

# Install secret detection
pip install detect-secrets
detect-secrets scan > .secrets.baseline

# Install dependency checkers
pip install safety
npm install -g npm-audit
```

## 📞 Security Contacts

- **Security Issues**: Create private security advisory in GitHub
- **Incident Response**: Contact repository owner immediately
- **Vulnerability Reports**: Use GitHub security tab

## 🎯 Security Principles

1. **Defense in Depth**: Multiple layers of security
2. **Least Privilege**: Minimal permissions needed
3. **Fail Secure**: Default to secure state
4. **Security by Design**: Build security in, not bolt on
5. **Regular Audits**: Continuous security monitoring

---

**Remember**: Security is everyone's responsibility. When in doubt, ask for help!
