# Generated by Django 2.2.6 on 2019-10-28 07:17

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('person', '0006_auto_20191026_1214'),
    ]

    operations = [
        migrations.CreateModel(
            name='Notification',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('unread', models.BooleanField(db_index=True, default=True)),
                ('date_created', models.DateTimeField(auto_now_add=True)),
                ('date_updated', models.DateTimeField(auto_now=True)),
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False)),
                ('slug', models.SlugField(blank=True, max_length=210, null=True)),
                ('verb', models.CharField(choices=[('T', 'dukung naik'), ('D', 'dukung turun'), ('C', 'berkomentar'), ('R', 'membalas')], max_length=1)),
                ('object_id', models.PositiveIntegerField()),
                ('actor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='notify_actor', to='person.Person')),
                ('content_type', models.ForeignKey(limit_choices_to=models.Q(app_label='notice'), on_delete=django.db.models.deletion.CASCADE, related_name='notify_action_object', to='contenttypes.ContentType')),
                ('recipient', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='notifications', to='person.Person')),
            ],
            options={
                'verbose_name': 'Notification',
                'verbose_name_plural': 'Notifications',
                'db_table': 'notice_notification',
                'ordering': ['-date_created'],
                'abstract': False,
            },
        ),
    ]