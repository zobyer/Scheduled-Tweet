# Generated by Django 4.0.6 on 2022-07-22 13:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('twitter', '0002_twitterschedulermodel_otp'),
    ]

    operations = [
        migrations.AddField(
            model_name='twitterschedulermodel',
            name='resource_owner_key',
            field=models.CharField(default='', max_length=50),
        ),
        migrations.AddField(
            model_name='twitterschedulermodel',
            name='resource_owner_secret',
            field=models.CharField(default='', max_length=50),
        ),
    ]