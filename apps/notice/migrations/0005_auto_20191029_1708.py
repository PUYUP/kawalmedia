# Generated by Django 2.2.6 on 2019-10-29 10:08

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('notice', '0004_auto_20191029_1706'),
    ]

    operations = [
        migrations.RenameField(
            model_name='notification',
            old_name='content_id',
            new_name='content_notified',
        ),
    ]
