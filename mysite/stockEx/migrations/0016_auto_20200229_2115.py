# Generated by Django 3.0.3 on 2020-02-29 13:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stockEx', '0015_userstockholding_stock_symbol'),
    ]

    operations = [
        migrations.AlterField(
            model_name='stock',
            name='price',
            field=models.FloatField(),
        ),
        migrations.AlterField(
            model_name='userdata',
            name='cash',
            field=models.FloatField(default=5000),
        ),
    ]
