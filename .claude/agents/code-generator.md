# 🖥️ Code Generator: Production Configuration and Best Practices

## 🚨 CRITICAL CONFIGURATION RULES

### 1. API URL Configuration

#### MANDATORY: Use Environment Variables
```typescript
// ✅ CORRECT
const API_BASE_URL = import.meta.env.VITE_API_URL;
axios.post(`${API_BASE_URL}/api/endpoint`, data);

// ❌ INCORRECT
axios.post('/api/endpoint', data);  // Never use relative paths
```

#### Environment Variable Best Practices
- Always prefix with `VITE_` for frontend
- Use `.env` files for different environments
- Never commit `.env` files with actual secrets
- Validate environment variables before use

### 2. Configuration Loading Strategy

```typescript
function validateEnvironment() {
  const requiredEnvVars = [
    'VITE_API_URL',
    'VITE_AUTH_PROVIDER',
    'VITE_FEATURE_FLAGS'
  ];

  requiredEnvVars.forEach(varName => {
    if (!import.meta.env[varName]) {
      throw new Error(`Missing critical environment variable: ${varName}`);
    }
  });
}

// Call this at app initialization
validateEnvironment();
```

### 3. Production vs Development Detection

```typescript
const isProduction = import.meta.env.PROD;
const isDevelopment = import.meta.env.DEV;

// Conditional logic based on environment
if (isProduction) {
  // Production-specific configurations
  configureProductionLogging();
  disableDevTools();
}

if (isDevelopment) {
  // Development-specific features
  enableDetailedLogging();
  setupMockServices();
}
```

### 4. Axios/Fetch Configuration

```typescript
const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL,
  timeout: 10000,  // 10-second timeout
  headers: {
    'Content-Type': 'application/json',
    'X-Environment': import.meta.env.VITE_ENVIRONMENT
  }
});

// Interceptors for global error handling
apiClient.interceptors.response.use(
  response => response,
  error => {
    // Centralized error logging and handling
    logProductionError(error);
    return Promise.reject(error);
  }
);
```

### 5. Feature Flag Management

```typescript
const featureFlags = {
  isNewAuthEnabled: import.meta.env.VITE_NEW_AUTH_ENABLED === 'true',
  isAIFeatureRollout: import.meta.env.VITE_AI_FEATURE_ROLLOUT === 'true'
};

function isFeatureEnabled(feature: keyof typeof featureFlags) {
  return featureFlags[feature];
}
```

## 🔒 Security Considerations

### Frontend Security Checklist
- [ ] No hardcoded API keys
- [ ] Use HTTPS for all API calls
- [ ] Implement proper CSRF protection
- [ ] Sanitize all user inputs
- [ ] Use secure, HttpOnly cookies for authentication

### Error Handling and Logging

```typescript
function safeApiCall(apiCall: () => Promise<any>) {
  try {
    return apiCall();
  } catch (error) {
    // Centralized, secure error handling
    if (import.meta.env.PROD) {
      // Log to secure, external service in production
      secureErrorLogging(error);
    }
    // User-friendly error message
    showUserFriendlyErrorNotification();
  }
}
```

## 🚦 Deployment Configuration Workflow

1. Local Development
   - Use `.env.development`
   - Full logging
   - Mock services

2. Staging Environment
   - Use `.env.staging`
   - Minimal logging
   - Real services, test configuration

3. Production Environment
   - Use `.env.production`
   - Minimal logging
   - Real services, production configuration

## 🔍 Pre-Deployment Verification

### Configuration Validation Script
```bash
#!/bin/bash
# config-validator.sh

# Check required environment variables
required_vars=(
  "VITE_API_URL"
  "VITE_AUTH_PROVIDER"
  "VITE_ENVIRONMENT"
)

for var in "${required_vars[@]}"; do
  if [ -z "${!var}" ]; then
    echo "❌ Missing required environment variable: $var"
    exit 1
  fi
done

echo "✅ All configuration variables validated successfully"
```

## 📋 Continuous Learning

- Regularly audit and rotate configurations
- Monitor and log configuration-related errors
- Update validation scripts
- Conduct periodic security reviews

---

*Last Updated: 2025-12-17*
*Maintainer: Claude Code Security Team*