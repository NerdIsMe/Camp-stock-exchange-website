# Generated by Django 3.0.3 on 2020-02-20 12:55

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('stockEx', '0005_remove_gamesetting_span'),
    ]

    operations = [
        migrations.CreateModel(
            name='Stock',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('stock_symbol', models.IntegerField()),
                ('company', models.CharField(max_length=20)),
                ('date_time', models.DateTimeField()),
                ('price', models.IntegerField()),
                ('growth_rate', models.FloatField()),
                ('volume', models.IntegerField(default=0)),
            ],
        ),
        migrations.CreateModel(
            name='HistStockData',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date_time', models.DateTimeField()),
                ('price', models.IntegerField()),
                ('growth_rate', models.FloatField()),
                ('volume', models.IntegerField(default=0)),
                ('belong', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='stockEx.Stock')),
            ],
        ),
    ]
