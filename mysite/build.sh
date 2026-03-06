#!/usr/bin/env bash
# exit on error
set -o errexit

# 1. Install dependencies
pip install -r requirements.txt

# 2. Collect static files
python manage.py collectstatic --no-input

# 3. Run database migrations
python manage.py migrate

# 4. Load your products (only if the file exists)
if [ -f products_backup.json ]; then
    echo "Loading initial product data..."
    python manage.py loaddata products_backup.json
fi

# 5. Create a superuser automatically (using Env Vars)
if [ "$CREATE_SUPERUSER" ]; then
    python manage.py createsuperuser --no-input || true
fi