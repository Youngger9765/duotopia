# 🔒 Security Hooks - DO NOT DELETE

## ⚠️ CRITICAL SECURITY INFRASTRUCTURE

These scripts are **ESSENTIAL SECURITY COMPONENTS** that run before every commit to prevent credential leaks.

## 📁 File Structure

```
.github/hooks/security/
├── README.md                  # This file
├── check-api-keys.sh         # Detects API keys (OpenAI, AWS, Google, etc.)
├── check-credentials.sh      # Detects hardcoded passwords
├── check-database-urls.sh    # Detects database connection strings
├── check-env-files.sh        # Prevents .env files from being committed
├── check-jwt-secrets.sh      # Detects JWT secrets
└── security-audit.sh         # Comprehensive security scan
```

## 🚨 WARNING

**DO NOT DELETE OR MODIFY THESE FILES** without understanding the security implications:

1. **Deletion = Security Breach Risk**: Without these checks, passwords and API keys could be committed
2. **Modification = False Negatives**: Incorrect changes could let credentials slip through
3. **Moving = Broken Hooks**: The paths are hardcoded in `.pre-commit-config.yaml`

## 🛡️ What These Scripts Protect Against

| Script | Protects Against | Example Pattern |
|--------|-----------------|-----------------|
| `check-api-keys.sh` | API key exposure | `sk-proj-xxxxx` (OpenAI) |
| `check-credentials.sh` | Hardcoded passwords | `password = "secret123"` |
| `check-database-urls.sh` | Database credentials | `postgresql://user:pass@host` |
| `check-env-files.sh` | Environment file commits | `.env`, `.env.staging` |
| `check-jwt-secrets.sh` | JWT secret exposure | `JWT_SECRET = "hardcoded"` |
| `security-audit.sh` | All of the above + more | Comprehensive scan |

## 🔧 How It Works

1. **Trigger**: Runs automatically on `git commit`
2. **Scan**: Searches all staged files for security patterns
3. **Block**: Prevents commit if issues found
4. **Report**: Shows exactly what was detected

## 📊 Statistics

- **Patterns Checked**: 15+ different credential types
- **File Types Scanned**: `.py`, `.ts`, `.tsx`, `.js`, `.json`, `.yml`, `Makefile`
- **Directories Excluded**: `node_modules`, `.git`, `.venv`
- **False Positive Filters**: `dummy`, `example`, `test`

## 🚀 Manual Testing

```bash
# Test individual script
./.github/hooks/security/check-api-keys.sh

# Run full security audit
./.github/hooks/security/security-audit.sh

# Test all pre-commit hooks
pre-commit run --all-files
```

## 🔄 Maintenance

### Adding New Patterns

Edit the relevant script and add to the pattern array:
```bash
API_KEY_PATTERNS=(
    "existing_pattern"
    "your_new_pattern"  # Add here
)
```

### Updating File Types

Add new extensions to the `--include` parameters:
```bash
--include="*.py" \
--include="*.ts" \
--include="*.newext" \  # Add here
```

## 📝 Version History

- **v1.0** (2024-01): Initial implementation
- **v1.1** (2024-09): Moved from `/scripts` to `/.github/hooks/security` for better protection

## ⚡ Performance

- **Average Scan Time**: < 2 seconds
- **Files Scanned**: ~500-1000 per commit
- **Memory Usage**: < 10MB
- **CPU Usage**: Single core

## 🐛 Troubleshooting

### Hook Not Running
```bash
# Reinstall pre-commit
pre-commit uninstall
pre-commit install
```

### Permission Denied
```bash
# Make scripts executable
chmod +x .github/hooks/security/*.sh
```

### False Positives
Add exclusions to the script:
```bash
grep -v "your_false_positive_context"
```

---

**Remember**: These scripts are your last line of defense against credential leaks. Treat them with respect! 🛡️
