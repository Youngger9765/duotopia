# Security Guidelines

## 🔐 Security Best Practices

### Environment Variables

1. **Never commit secrets to version control**
   - All `.env` files are gitignored
   - Use `.env.example` files as templates
   - Generate secure secrets using: `openssl rand -hex 32`

2. **Required Environment Variables**
   - `DATABASE_URL` - PostgreSQL connection string
   - `SECRET_KEY` - JWT signing key (must be secure)
   - `GOOGLE_CLIENT_ID` - OAuth client ID
   - `GOOGLE_CLIENT_SECRET` - OAuth client secret
   - `OPENAI_API_KEY` - OpenAI API key

3. **Local Development**
   - Copy `.env.example` to `.env` in each directory
   - Use `docker-compose.override.yml` for local Docker settings
   - Never use default passwords in production

### Google Cloud Security

1. **Secret Manager**
   - All production secrets stored in Google Secret Manager
   - Access controlled via IAM roles
   - Automatic rotation supported

2. **Service Accounts**
   - Follow least privilege principle
   - Separate accounts for different services
   - No service account keys in code

3. **Network Security**
   - Cloud SQL uses private IP
   - VPC connector for Cloud Run
   - Firewall rules restrict access

### Authentication & Authorization

1. **Password Security**
   - Bcrypt for password hashing
   - No plain text passwords
   - Strong password requirements

2. **JWT Tokens**
   - Short expiration times (30 minutes)
   - Secure random keys
   - HTTPS only transmission

3. **OAuth 2.0**
   - Google OAuth for teachers
   - Proper redirect URI validation
   - State parameter for CSRF protection

### Data Protection

1. **Input Validation**
   - All user inputs validated
   - SQL injection prevention via ORM
   - XSS protection in React

2. **HTTPS Everywhere**
   - SSL/TLS for all communications
   - HSTS headers enabled
   - Certificate pinning for mobile apps

3. **Data Encryption**
   - Encryption at rest (Cloud SQL)
   - Encryption in transit (TLS)
   - Sensitive data masked in logs

### Monitoring & Incident Response

1. **Logging**
   - Structured logging to Cloud Logging
   - No sensitive data in logs
   - Audit trail for admin actions

2. **Alerting**
   - Failed login attempts monitoring
   - Unusual API activity detection
   - Resource usage alerts

3. **Incident Response**
   - Security contact: security@duotopia.com
   - 24-hour response time for critical issues
   - Regular security audits

### Development Security

1. **Code Review**
   - All PRs require security review
   - Automated security scanning
   - Dependency vulnerability checks

2. **Testing**
   - Security test cases
   - Penetration testing yearly
   - OWASP Top 10 compliance

3. **Dependencies**
   - Regular updates
   - Vulnerability scanning
   - License compliance

## 🚨 Reporting Security Issues

If you discover a security vulnerability, please:

1. **DO NOT** open a public issue
2. Email security@duotopia.com with details
3. Include steps to reproduce
4. Allow 48 hours for initial response

We appreciate responsible disclosure and will acknowledge your contribution.