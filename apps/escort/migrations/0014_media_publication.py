# Generated by Django 2.2.6 on 2019-10-24 14:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('escort', '0013_auto_20191024_1200'),
    ]

    operations = [
        migrations.AddField(
            model_name='media',
            name='publication',
            field=models.PositiveIntegerField(choices=[((1, 'Electronic'), ((1, 'Television'), (2, 'Radio'))), ((3, 'Online'), ((3, 'YouTube'), (4, 'Blog'), (5, 'News Site'))), ((2, 'Printed'), ((6, 'Newspaper'), (7, 'Magazine')))], default=1),
        ),
    ]
