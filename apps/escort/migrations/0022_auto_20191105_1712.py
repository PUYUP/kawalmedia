# Generated by Django 2.2.6 on 2019-11-05 10:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('escort', '0021_auto_20191031_1845'),
    ]

    operations = [
        migrations.AddField(
            model_name='attributevalue',
            name='date_created',
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
        migrations.AddField(
            model_name='attributevalue',
            name='date_updated',
            field=models.DateTimeField(auto_now=True, null=True),
        ),
    ]