from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('settingsapp', '0004_systemsettings_telegram_reports'),
    ]

    operations = [
        migrations.AddField(
            model_name='systemsettings',
            name='telegram_last_report_date',
            field=models.DateField(blank=True, null=True),
        ),
    ]
