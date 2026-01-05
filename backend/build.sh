#!/usr/bin/env bash
# Build script for Koyeb deployment
# Note: pip install is handled by Koyeb buildpack, collectstatic too

set -o errexit

# Run database migrations
python manage.py migrate --noinput
