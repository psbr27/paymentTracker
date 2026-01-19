# Security Setup Guide

## Overview
This project has been configured with security scanning to prevent accidentally committing sensitive information.

## What's Been Set Up

### 1. .gitignore Updates
- Added `docs/` directory to .gitignore
- `.env` files are already excluded

### 2. Environment Variables
A `.env.example` file has been created showing all required configuration.

**To set up your environment:**
```bash
# Copy the example file
cp .env.example .env

# Generate a secure JWT secret
python3 -c 'import secrets; print(secrets.token_urlsafe(32))'

# Edit .env and replace the JWT_SECRET_KEY with the generated value
nano .env
```

### 3. Pre-commit Hooks
The following security checks run before each commit:

- **detect-private-key**: Prevents committing SSH/SSL private keys
- **detect-secrets**: Scans for API keys, passwords, tokens
- **gitleaks**: Additional credential scanning
- **check-added-large-files**: Prevents large files (>1MB)
- **check-yaml**: Validates YAML syntax
- **trailing-whitespace**: Cleans up whitespace
- **end-of-file-fixer**: Ensures proper line endings

## Installation

Run the security setup script:
```bash
./setup_security.sh
```

This will:
1. Install pip (if needed)
2. Install pre-commit and detect-secrets
3. Create a secrets baseline
4. Install git hooks

## Current Security Issues

⚠️ **CRITICAL: Hardcoded JWT Secret**

Location: `backend/app/config.py`
```python
jwt_secret_key: str = "your-super-secret-key-change-in-production"
```

**Fix:**
1. Remove the default value from config.py
2. Set it in your .env file instead
3. The pydantic BaseSettings will automatically load from .env

**Updated config.py:**
```python
class Settings(BaseSettings):
    # JWT - NO DEFAULT, MUST BE SET IN .env
    jwt_secret_key: str  # Required from environment
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440
```

## Daily Usage

Once installed, pre-commit hooks run automatically. If a secret is detected:

```bash
$ git commit -m "Add feature"
Detect secrets...........................................................Failed
```

To bypass (NOT recommended):
```bash
git commit --no-verify -m "message"
```

## Manual Security Scan

Run security checks manually:
```bash
# Scan for secrets
detect-secrets scan

# Run all pre-commit hooks
pre-commit run --all-files

# Update hooks to latest versions
pre-commit autoupdate
```

## Best Practices

1. **Never commit**:
   - API keys, tokens, passwords
   - Database credentials
   - Private keys
   - `.env` files

2. **Always**:
   - Use environment variables for secrets
   - Keep `.env.example` updated
   - Review pre-commit warnings
   - Rotate secrets if accidentally committed

3. **If you accidentally commit a secret**:
   ```bash
   # Remove from git history
   git filter-branch --force --index-filter \
     "git rm --cached --ignore-unmatch PATH/TO/FILE" \
     --prune-empty --tag-name-filter cat -- --all

   # Rotate the compromised secret immediately!
   ```

## Additional Tools

Consider adding:
- **Trivy**: Container and dependency scanning
- **Bandit**: Python security linter
- **Safety**: Python dependency vulnerability checker

```bash
pip install bandit safety
bandit -r backend/
safety check
```
