# Generated by Django 2.2.6 on 2019-10-31 10:20

import apps.person.models.models_validation
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion
import utils.validators
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('person', '0006_auto_20191026_1214'),
    ]

    operations = [
        migrations.CreateModel(
            name='Validation',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False)),
                ('label', models.CharField(max_length=128, verbose_name='Label')),
                ('identifier', models.SlugField(max_length=128, validators=[django.core.validators.RegexValidator(message="Code can only contain the letters a-z, A-Z, digits, and underscores, and can't start with a digit.", regex='^[a-zA-Z_][0-9a-zA-Z_]*$'), utils.validators.non_python_keyword], verbose_name='Identifier')),
                ('field_type', models.CharField(choices=[('text', 'Text'), ('url', 'URL'), ('integer', 'Integer'), ('richtext', 'Rich Text'), ('file', 'File'), ('image', 'Image')], default='text', max_length=20, verbose_name='Type')),
                ('secured', models.BooleanField(default=False, verbose_name='Secured')),
                ('required', models.BooleanField(default=False, verbose_name='Required')),
                ('content_type', models.ManyToManyField(blank=True, limit_choices_to=models.Q(app_label='person'), related_name='person_validation', to='contenttypes.ContentType')),
                ('roles', models.ManyToManyField(blank=True, help_text='Limit validations by Roles.', limit_choices_to=models.Q(is_active=True), to='person.Role')),
            ],
            options={
                'verbose_name': 'Validation',
                'verbose_name_plural': 'Validations',
                'db_table': 'person_validation',
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='ValidationValue',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False)),
                ('value_text', models.CharField(blank=True, max_length=255, null=True, verbose_name='Text')),
                ('value_url', models.URLField(blank=True, max_length=500, null=True, verbose_name='URL')),
                ('value_integer', models.IntegerField(blank=True, db_index=True, null=True, verbose_name='Integer')),
                ('value_richtext', models.TextField(blank=True, null=True, verbose_name='Richtext')),
                ('value_file', models.FileField(blank=True, max_length=255, null=True, upload_to=apps.person.models.models_validation.entity_directory_file_path)),
                ('value_image', models.ImageField(blank=True, max_length=255, null=True, upload_to=apps.person.models.models_validation.entity_directory_image_path)),
                ('object_id', models.PositiveIntegerField(blank=True, null=True)),
                ('content_type', models.ForeignKey(blank=True, limit_choices_to=models.Q(app_label='person'), null=True, on_delete=django.db.models.deletion.CASCADE, related_name='person_entity_validation', to='contenttypes.ContentType')),
                ('validation', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='person.Validation', verbose_name='Validation')),
            ],
            options={
                'verbose_name': 'Validation value',
                'verbose_name_plural': 'Validation values',
                'db_table': 'person_validation_value',
                'abstract': False,
                'unique_together': {('validation', 'content_type', 'object_id')},
            },
        ),
    ]
