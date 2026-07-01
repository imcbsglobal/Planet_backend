from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('feeder', '0006_add_modules_field'),
    ]

    operations = [
        migrations.AddField(
            model_name='feeder',
            name='corporate',
            field=models.CharField(max_length=255, blank=True, null=True),
        ),
    ]
