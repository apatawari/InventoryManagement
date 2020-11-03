# Generated by Django 3.1.2 on 2020-11-03 07:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventoryapp', '0003_auto_20201102_2239'),
    ]

    operations = [
        migrations.CreateModel(
            name='ArrivalLocation',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('location', models.CharField(max_length=50)),
            ],
        ),
        migrations.AddField(
            model_name='record',
            name='arrival_location',
            field=models.CharField(default='-', max_length=50),
        ),
        migrations.AddField(
            model_name='record',
            name='processing_type',
            field=models.CharField(default='-', max_length=50),
        ),
    ]
