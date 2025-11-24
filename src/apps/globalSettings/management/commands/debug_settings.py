# src/apps/globalSettings/management/commands/debug_settings.py
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = 'Debug config module import'

    def handle(self, *args, **options):
        self.stdout.write('=== Debugging Config Import ===\n')

        # Test 1: Import config module
        try:
            import config
            self.stdout.write(f'✓ config module imported: {config}')
            self.stdout.write(f'  config.__file__: {config.__file__}')
            self.stdout.write(f'  config.__name__: {config.__name__}')
        except ImportError as e:
            self.stdout.write(self.style.ERROR(f'✗ Failed to import config: {e}'))
            return

        # Test 2: Check for settings attribute
        if hasattr(config, 'settings'):
            self.stdout.write(f'✓ config.settings exists')
            settings_obj = config.settings
            self.stdout.write(f'  Type: {type(settings_obj)}')
            self.stdout.write(f'  Module: {type(settings_obj).__module__}')
            self.stdout.write(f'  Class: {type(settings_obj).__name__}')
        else:
            self.stdout.write(self.style.ERROR('✗ config.settings does not exist'))
            self.stdout.write(f'  Available attributes: {[a for a in dir(config) if not a.startswith("_")]}')
            return

        # Test 3: Check if it's a Pydantic model
        if hasattr(settings_obj, '__fields__'):
            self.stdout.write(f'✓ settings is a Pydantic model')
            self.stdout.write(f'  Number of fields: {len(settings_obj.__fields__)}')
            self.stdout.write(f'  Sample fields: {list(settings_obj.__fields__.keys())[:5]}')
        else:
            self.stdout.write(self.style.ERROR('✗ settings is NOT a Pydantic model'))
            self.stdout.write(f'  Available attributes: {[a for a in dir(settings_obj) if not a.startswith("_")][:10]}')

        # Test 4: Check specific values
        try:
            self.stdout.write(f'\n✓ Sample values:')
            self.stdout.write(f'  site_title: {settings_obj.site_title}')
            self.stdout.write(f'  debug: {settings_obj.debug}')
            self.stdout.write(f'  version: {settings_obj.version}')
        except AttributeError as e:
            self.stdout.write(self.style.ERROR(f'✗ Error accessing attributes: {e}'))

        # Test 5: Check Django settings
        self.stdout.write(f'\n=== Django Settings ===')
        from django.conf import settings as django_settings
        self.stdout.write(f'django.conf.settings: {django_settings}')
        self.stdout.write(f'Type: {type(django_settings)}')

        # Test 6: Check sys.modules
        import sys
        self.stdout.write(f'\n=== sys.modules ===')
        if 'config' in sys.modules:
            self.stdout.write(f'✓ config in sys.modules: {sys.modules["config"]}')
        else:
            self.stdout.write(self.style.ERROR('✗ config NOT in sys.modules'))

        if 'config.settings' in sys.modules:
            self.stdout.write(f'⚠ config.settings in sys.modules: {sys.modules["config.settings"]}')
            self.stdout.write(f'  This might be Django settings shadowing!')