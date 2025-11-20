# Development Setup Guide

This guide will help you set up a development environment for PDA-Next.

## Quick Start

1. **Use the development settings:**
   ```bash
   # Use the development management script
   python src/manage_dev.py runserver
   
   # Or set the environment variable manually
   export DJANGO_SETTINGS_MODULE=pda.settings_dev
   python src/manage.py runserver
   ```

2. **Create a development environment file (optional):**
   Create a `.env.dev` file in the project root with your development settings:
   ```bash
   cp .env.dev.example .env.dev  # If example exists
   # Or create manually - see configuration options below
   ```

## Configuration Options

You can customize development settings via environment variables or a `.env.dev` file:

### Basic Development Settings

```bash
# Environment type
PDA_ENV_TYPE=development

# Debug mode
PDA_DEBUG=true

# Secret key (use a simple one for dev)
PDA_SECRET_KEY=dev-secret-key-change-in-production-12345

# Database (SQLite is default and recommended for dev)
PDA_DB_ENGINE=sqlite
PDA_DB_PATH=db.sqlite3

# Or use PostgreSQL/MySQL
PDA_DB_ENGINE=postgresql
PDA_DB_HOST=localhost
PDA_DB_PORT=5432
PDA_DB_NAME=pda_dev
PDA_DB_USER=pda_dev
PDA_DB_PASSWORD=dev_password
```

### Security Settings (Disabled for Development)

```bash
PDA_SECURE_SSL_REDIRECT=false
PDA_SESSION_COOKIE_SECURE=false
PDA_CSRF_COOKIE_SECURE=false
PDA_USE_HTTPS_IN_ABSOLUTE_URLS=false
```

### Email Configuration

Emails are automatically sent to console in development. To use SMTP instead:

```bash
PDA_EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
PDA_EMAIL_HOST=smtp.gmail.com
PDA_EMAIL_PORT=587
PDA_EMAIL_USE_TLS=true
PDA_EMAIL_HOST_USER=your-email@gmail.com
PDA_EMAIL_HOST_PASSWORD=your-app-password
```

### PowerDNS API Configuration

```bash
PDA_POWERDNS_API_URL=http://localhost:8081/api/v1
PDA_POWERDNS_API_KEY=your-api-key-here
PDA_POWERDNS_API_TIMEOUT=30
```

## Common Development Tasks

### Running the Development Server

```bash
python src/manage_dev.py runserver
# Or with custom port
python src/manage_dev.py runserver 8080
```

### Running Migrations

```bash
python src/manage_dev.py migrate
```

### Creating a Superuser

```bash
python src/manage_dev.py createsuperuser
```

### Creating Migrations

```bash
python src/manage_dev.py makemigrations
```

### Accessing the Debug Toolbar

The debug toolbar is automatically enabled in development mode. It will appear on the right side of pages when:
- You're accessing from `127.0.0.1` or `localhost`
- DEBUG mode is enabled

### Viewing SQL Queries

All SQL queries are automatically logged to the console in development mode. Look for output like:
```
(0.001) SELECT ... FROM ...; args=()
```

## Troubleshooting

### Debug Toolbar Not Showing

1. Make sure you're accessing from `127.0.0.1` or `localhost` (not `0.0.0.0`)
2. Check that `DEBUG = True` in your settings
3. Verify `debug_toolbar` is in `INSTALLED_APPS`
4. Check browser console for any JavaScript errors

### Database Issues

If you have database connection issues:
1. For SQLite: Make sure the directory is writable
2. For PostgreSQL/MySQL: Verify credentials and that the database exists
3. Run migrations: `python src/manage_dev.py migrate`

### Static Files Not Loading

Collect static files:
```bash
python src/manage_dev.py collectstatic --noinput
```

Or use Django's development server which serves static files automatically.

## Differences from Production

The development settings differ from production in these ways:

| Setting | Development | Production |
|---------|------------|------------|
| DEBUG | True | False |
| Database | SQLite (default) | PostgreSQL/MySQL |
| Email Backend | Console | SMTP |
| Security Headers | Disabled | Enabled |
| Logging Level | DEBUG | INFO/WARNING |
| Email Verification | Disabled | Enabled |
| Secret Key | Simple dev key | Secure random key |

## Next Steps

- See [Configuration Guide](../wiki/configuration/README.md) for all available settings
- See [Testing Guide](../wiki/testing/README.md) for running tests
- See [Contributing Guide](../wiki/contributing/README.md) for development guidelines

