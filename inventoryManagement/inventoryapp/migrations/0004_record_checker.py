# Generated by Django 3.1.2 on 2020-11-26 06:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventoryapp', '0003_thanrange'),
    ]

    operations = [
        migrations.AddField(
            model_name='record',
            name='checker',
            field=models.CharField(default='-', max_length=50),
        ),
    ]