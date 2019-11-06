# Generated by Django 2.2.6 on 2019-10-30 02:03

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('notice', '0007_auto_20191030_0754'),
    ]

    operations = [
        migrations.AddField(
            model_name='notification',
            name='content_parent_id',
            field=models.PositiveIntegerField(null=True),
        ),
        migrations.AddField(
            model_name='notification',
            name='content_parent_type',
            field=models.ForeignKey(limit_choices_to=models.Q(app_label__in=['escort', 'person']), null=True, on_delete=django.db.models.deletion.CASCADE, related_name='notice_entity_notification_parent', to='contenttypes.ContentType'),
        ),
        migrations.AlterField(
            model_name='notification',
            name='content_notified_type',
            field=models.ForeignKey(limit_choices_to=models.Q(app_label__in=['escort', 'person']), null=True, on_delete=django.db.models.deletion.CASCADE, related_name='notice_entity_notification_notified', to='contenttypes.ContentType'),
        ),
        migrations.AlterField(
            model_name='notification',
            name='content_source_type',
            field=models.ForeignKey(limit_choices_to=models.Q(app_label__in=['escort', 'person']), null=True, on_delete=django.db.models.deletion.CASCADE, related_name='notice_entity_notification_source', to='contenttypes.ContentType'),
        ),
    ]