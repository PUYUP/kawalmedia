# Generated by Django 2.2.6 on 2019-10-28 11:27

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('escort', '0019_auto_20191027_1754'),
    ]

    operations = [
        migrations.AlterField(
            model_name='comment',
            name='parent',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='parent_comment', to='escort.Comment', verbose_name='Parent comment'),
        ),
    ]
