from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0007_historicalorder_waiter_order_waiter'),
    ]

    operations = [
        migrations.AddField(
            model_name='historicalorderitem',
            name='kitchen_status',
            field=models.CharField(
                choices=[
                    ('draft', 'Draft'),
                    ('waiting', 'Waiting'),
                    ('preparing', 'Preparing'),
                    ('ready', 'Ready'),
                    ('served', 'Served'),
                    ('cancelled', 'Cancelled'),
                ],
                default='draft',
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name='historicalorderitem',
            name='sent_to_kitchen_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='orderitem',
            name='kitchen_status',
            field=models.CharField(
                choices=[
                    ('draft', 'Draft'),
                    ('waiting', 'Waiting'),
                    ('preparing', 'Preparing'),
                    ('ready', 'Ready'),
                    ('served', 'Served'),
                    ('cancelled', 'Cancelled'),
                ],
                default='draft',
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name='orderitem',
            name='sent_to_kitchen_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
