from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('settingsapp', '0003_systemsettings_rub_to_base_rate_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='systemsettings',
            name='telegram_bot_token',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='systemsettings',
            name='telegram_chat_id',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='systemsettings',
            name='telegram_report_time',
            field=models.TimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='systemsettings',
            name='telegram_reports_enabled',
            field=models.BooleanField(default=False),
        ),
    ]
