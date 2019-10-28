# Generated by Django 2.2.6 on 2019-10-08 15:41

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('person', '0003_auto_20191008_2241'),
        ('contenttypes', '0002_remove_content_type_name'),
        ('escort', '0003_auto_20191008_0945'),
    ]

    operations = [
        migrations.CreateModel(
            name='EntityLog',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False)),
                ('status', models.PositiveIntegerField(choices=[(1, 'Pending'), (2, 'Reviewed'), (3, 'Published'), (4, 'Returned'), (5, 'Rejected'), (6, 'Draft')], default=1)),
                ('description', models.TextField(blank=True, null=True)),
                ('date_created', models.DateTimeField(auto_now_add=True)),
                ('date_updated', models.DateTimeField(auto_now=True)),
                ('object_id', models.PositiveIntegerField(blank=True, editable=False, null=True)),
                ('content_type', models.ForeignKey(blank=True, editable=False, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='escort_entity_attibutes', to='contenttypes.ContentType')),
                ('logger', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='logger', to='person.Person')),
            ],
            options={
                'verbose_name': 'Entity log',
                'verbose_name_plural': 'Entity log',
                'db_table': 'escort_entity_log',
                'abstract': False,
            },
        ),
        migrations.RemoveField(
            model_name='protestprocess',
            name='processor',
        ),
        migrations.RemoveField(
            model_name='protestprocess',
            name='protest',
        ),
        migrations.AlterField(
            model_name='attachment',
            name='content_type',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='escort_entity_attachment', to='contenttypes.ContentType'),
        ),
        migrations.DeleteModel(
            name='MediaProcess',
        ),
        migrations.DeleteModel(
            name='ProtestProcess',
        ),
    ]