#!/bin/bash

echo "Setting up security tools for paymentTracker..."

# Install pip if not available
if ! command -v pip &> /dev/null && ! python3 -m pip --version &> /dev/null; then
    echo "Installing pip..."
    sudo apt update
    sudo apt install -y python3-pip
fi

# Install pre-commit and security tools
echo "Installing pre-commit and security scanning tools..."
python3 -m pip install --user pre-commit detect-secrets

# Initialize detect-secrets baseline
echo "Creating secrets baseline..."
detect-secrets scan > .secrets.baseline

# Install pre-commit hooks
echo "Installing pre-commit hooks..."
pre-commit install

echo ""
echo "✅ Security setup complete!"
echo ""
echo "Pre-commit hooks installed:"
echo "  - Private key detection"
echo "  - Secret scanning (detect-secrets)"
echo "  - Gitleaks (credential scanning)"
echo "  - File size checks"
echo "  - YAML validation"
echo ""
echo "⚠️  IMPORTANT SECURITY ISSUES FOUND:"
echo "  1. Hardcoded JWT secret in backend/app/config.py"
echo "     → Move to .env file and use environment variables"
echo ""
echo "Next steps:"
echo "  1. Create a .env file based on .env.example"
echo "  2. Generate a secure JWT secret: python3 -c 'import secrets; print(secrets.token_urlsafe(32))'"
echo "  3. Update backend/app/config.py to remove default secret value"
echo "  4. Add .env to .gitignore (already done)"
