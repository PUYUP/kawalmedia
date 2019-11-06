# Generated by Django 2.2.6 on 2019-10-28 11:14

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('notice', '0002_auto_20191028_1644'),
    ]

    operations = [
        migrations.AddField(
            model_name='notificationactor',
            name='notification',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='notify_actor_object', to='notice.Notification'),
        ),
        migrations.AddField(
            model_name='notificationrecipient',
            name='notification',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='notify_recipient_object', to='notice.Notification'),
        ),
        migrations.AlterField(
            model_name='notification',
            name='content_type',
            field=models.ForeignKey(limit_choices_to=models.Q(app_label__in=['escort', 'person']), on_delete=django.db.models.deletion.CASCADE, related_name='notice_entity_notification', to='contenttypes.ContentType'),
        ),
    ]
