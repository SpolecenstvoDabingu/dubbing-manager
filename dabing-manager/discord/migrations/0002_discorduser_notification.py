# Generated by Django 5.2.4 on 2025-07-26 13:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('discord', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='discorduser',
            name='notification',
            field=models.BooleanField(default=False),
        ),
    ]
