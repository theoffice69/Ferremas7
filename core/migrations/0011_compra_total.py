# Generated by Django 3.1.2 on 2024-05-26 23:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0010_auto_20240523_2054'),
    ]

    operations = [
        migrations.AddField(
            model_name='compra',
            name='total',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10),
        ),
    ]