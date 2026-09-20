#!/bin/sh
set -eu

base64_value() {
  printf '%s' "$1" | base64 | tr -d '\n'
}

api_base_url="${API_BASE_URL:-http://localhost:8000/api}"
decart_public_key="${DECART_PUBLIC_KEY:-}"
stripe_publishable_key="${STRIPE_PUBLISHABLE_KEY:-}"

cat > /usr/share/nginx/html/runtime-config.js <<EOF
window.__runtimeConfig = {
  apiBaseUrl: atob('$(base64_value "$api_base_url")'),
  decartApiKey: atob('$(base64_value "$decart_public_key")'),
  stripePublishableKey: atob('$(base64_value "$stripe_publishable_key")'),
};
EOF

exec "$@"
