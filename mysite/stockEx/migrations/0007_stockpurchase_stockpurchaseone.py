# Generated by Django 3.0.3 on 2020-02-23 04:29

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('stockEx', '0006_histstockdata_stock'),
    ]

    operations = [
        migrations.CreateModel(
            name='StockPurchase',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date_time', models.DateTimeField()),
                ('amount', models.IntegerField()),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='StockPurchaseOne',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('company', models.CharField(max_length=20)),
                ('quantity', models.IntegerField()),
                ('amount', models.IntegerField()),
                ('stock_purchase', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='stockEx.StockPurchase')),
            ],
        ),
    ]
