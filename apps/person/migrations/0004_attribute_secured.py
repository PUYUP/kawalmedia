# Generated by Django 2.2.6 on 2019-10-11 01:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('person', '0003_auto_20191008_2241'),
    ]

    operations = [
        migrations.AddField(
            model_name='attribute',
            name='secured',
            field=models.BooleanField(default=False, verbose_name='Secured'),
        ),
    ]
