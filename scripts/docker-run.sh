#!/bin/bash

set -e

echo "=== Starting docker-run.sh ==="

# Run collectstatic
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Set default TENANTS if not provided or empty
if [ -z "$TENANTS" ]; then
  TENANTS="default"
  echo "TENANTS not set. Using default: $TENANTS"
else
  echo "TENANTS set to: $TENANTS"
fi

# Split TENANTS and run migrations
IFS=',' read -ra TENANT_ARRAY <<< "$TENANTS"
for tenant in "${TENANT_ARRAY[@]}"; do
  echo "⚙️ Running migrations for tenant: $tenant"
  python manage.py migrate --noinput --database="$tenant" || {
    echo "Migration failed for tenant: $tenant"
    exit 1
  }
done

# Start Gunicorn
echo "Starting Gunicorn..."
gunicorn -b 0.0.0.0:8000 --worker-class=gevent --workers=8 user_portfolio.wsgi:application
