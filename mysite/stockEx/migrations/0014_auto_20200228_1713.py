# Generated by Django 3.0.3 on 2020-02-28 09:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stockEx', '0013_auto_20200227_1259'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userstockholding',
            name='average_cost',
            field=models.FloatField(),
        ),
        migrations.AlterField(
            model_name='userstockholding',
            name='total_cost',
            field=models.FloatField(),
        ),
    ]
