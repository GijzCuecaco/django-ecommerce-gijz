#!/usr/bin/env bash
# exit on error
set -o errexit

echo "--- STARTING BUILD ---"

# This forces the install and shows you if it fails
pip install --upgrade pip
pip install -r requirements.txt

echo "--- INSTALL COMPLETE ---"

# This checks if the driver actually installed
python -c "import psycopg2; print('Psycopg2 is ready!')"

python manage.py collectstatic --no-input
python manage.py migrate

if [ -f products_backup.json ]; then
    echo "--- LOADING DATA ---"
    python manage.py loaddata products_backup.json
fi