# Django E-commerce Project

This repository contains a simple e-commerce application built with Django 6.0.

## Preparing for Deployment

1. **Environment variables**
   - Create a copy of `.env.example` named `.env` in the project root.
   - Fill in at least:
     ```text
     DJANGO_SECRET_KEY=<a long random string>
     DJANGO_DEBUG=False
     DJANGO_ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
     ```
   - Optionally set the security variables:
     `DJANGO_SECURE_HSTS_SECONDS`, `DJANGO_SECURE_SSL_REDIRECT`, 
     `DJANGO_SESSION_COOKIE_SECURE` and `DJANGO_CSRF_COOKIE_SECURE`.

2. **Install dependencies**
   ```bash
   python -m venv .venv
   . .venv/Scripts/activate   # Windows
   pip install -r requirements.txt
   ```

3. **Configure database**
   - The project reads `DATABASE_URL` (e.g. `postgres://...`) via `dj-database-url`.
   - If not set it falls back to a local `sqlite3` database stored at `db.sqlite3`.

4. **Collect static files**
   ```bash
   python manage.py collectstatic --noinput
   ```
   Whitenoise is configured to serve compressed static assets.

5. **Run deployment checks**
   ```bash
   python manage.py check --deploy
   ```
   Address any warnings by adjusting environment variables or settings.

6. **Platform-specific files**
   - `Procfile` (Heroku) contains: `web: gunicorn mysite.wsgi`
   - `runtime.txt` pins the Python version.
   - `.gitignore` filters out database, secrets, and build artifacts.

7. **Starting the server**
   ```bash
   gunicorn mysite.wsgi
   ```
   or use the hosting platform's mechanism.


## Additional Notes

- Debug is default to `False` in production; never commit `DEBUG=True`.
- Secret key should be at least 50 characters and not start with `django-insecure-`.
- Always run migrations before starting the server:
  ```bash
  python manage.py migrate
  ```

For more details consult the [official Django deployment checklist](https://docs.djangoproject.com/en/6.0/howto/deployment/).
