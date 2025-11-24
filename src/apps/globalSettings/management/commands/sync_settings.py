from django.core.management.base import BaseCommand
from apps.globalSettings.utils import sync_env_settings_to_db

class Command(BaseCommand):
    help = 'Sync settings from environment/config file to database'

    def handle(self, *args, **options):
        self.stdout.write('Syncing settings to database...')
        count = sync_env_settings_to_db()
        self.stdout.write(
            self.style.SUCCESS(f'Successfully synced {count} settings to database')
        )