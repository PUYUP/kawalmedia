# Generated by Django 2.2.6 on 2019-10-29 10:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('notice', '0003_auto_20191028_1814'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='notification',
            name='slug',
        ),
        migrations.AddField(
            model_name='notification',
            name='content_id',
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
    ]
