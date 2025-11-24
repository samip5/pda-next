from django.db import migrations, models

class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='GlobalSetting',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('key', models.CharField(db_index=True, max_length=255, unique=True)),
                ('value', models.TextField()),
                ('setting_type', models.CharField(choices=[('string', 'String'), ('integer', 'Integer'), ('boolean', 'Boolean'), ('float', 'Float'), ('json', 'JSON')], default='string', max_length=20)),
                ('description', models.TextField(blank=True, help_text='Description of this setting')),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name': 'Global Setting',
                'verbose_name_plural': 'Global Settings',
                'ordering': ['key'],
            },
        ),
    ]

