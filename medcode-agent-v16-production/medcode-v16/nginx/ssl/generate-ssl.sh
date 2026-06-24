#!/bin/bash
# Generate self-signed SSL certificate for development only
# Production should use Let's Encrypt (certbot)

set -euo pipefail

SSL_DIR="$(cd "$(dirname "$0")" && pwd)"
CERT_FILE="${SSL_DIR}/fullchain.pem"
KEY_FILE="${SSL_DIR}/privkey.pem"

if [ -f "$CERT_FILE" ] && [ -f "$KEY_FILE" ]; then
    echo "SSL certificates already exist. Remove them to regenerate."
    echo "  $CERT_FILE"
    echo "  $KEY_FILE"
    exit 0
fi

echo "Generating self-signed SSL certificate for development..."

openssl req -x509 -nodes -days 365 \
    -newkey rsa:2048 \
    -keyout "$KEY_FILE" \
    -out "$CERT_FILE" \
    -subj "/C=US/ST=State/L=City/O=MedCode/CN=localhost" \
    -addext "subjectAltName=DNS:localhost,IP:127.0.0.1"

chmod 600 "$KEY_FILE"
chmod 644 "$CERT_FILE"

echo "SSL certificates generated:"
echo "  Certificate: $CERT_FILE"
echo "  Private Key: $KEY_FILE"
echo ""
echo "For production, use Let's Encrypt:"
echo "  certbot certonly --webroot -w /var/www/certbot -d yourdomain.com"
