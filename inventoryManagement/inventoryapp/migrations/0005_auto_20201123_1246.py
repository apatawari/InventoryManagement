# Generated by Django 3.1.2 on 2020-11-23 07:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventoryapp', '0004_colorrecord_chalan_no'),
    ]

    operations = [
        migrations.AddField(
            model_name='allorders',
            name='bill_date',
            field=models.DateField(default=None, null=True),
        ),
        migrations.AddField(
            model_name='allorders',
            name='bill_no',
            field=models.IntegerField(null=True),
        ),
    ]