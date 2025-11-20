#!/usr/bin/env python
"""
Development management script for PDA project.

This script automatically uses the development settings (pda.settings_dev).
Usage is identical to manage.py, e.g.:
    python manage_dev.py runserver
    python manage_dev.py migrate
    python manage_dev.py createsuperuser
"""
import os
import sys

if __name__ == "__main__":
    # Use development settings by default
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "pda.settings_dev")
    
    # Set development environment type if not already set
    if 'PDA_ENV_TYPE' not in os.environ:
        os.environ['PDA_ENV_TYPE'] = 'development'
    
    # Use a local .env file for development if it exists
    dev_env_file = os.path.join(os.path.dirname(__file__), '..', '.env.dev')
    if os.path.exists(dev_env_file):
        os.environ['PDA_ENV_FILE'] = dev_env_file
    
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)

