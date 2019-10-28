# Generated by Django 2.2.6 on 2019-10-07 10:14

import apps.person.models.models_attribute
from django.conf import settings
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion
import utils.validators
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('contenttypes', '0002_remove_content_type_name'),
    ]

    operations = [
        migrations.CreateModel(
            name='AttributeOptionGroup',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False)),
                ('label', models.CharField(max_length=128, verbose_name='Label')),
                ('identifier', models.SlugField(max_length=128, null=True, validators=[django.core.validators.RegexValidator(message="Code can only contain the letters a-z, A-Z, digits, and underscores, and can't start with a digit.", regex='^[a-zA-Z_][0-9a-zA-Z_]*$'), utils.validators.non_python_keyword], verbose_name='Identifier')),
            ],
            options={
                'verbose_name': 'Attribute option group',
                'verbose_name_plural': 'Attribute option groups',
                'db_table': 'person_attribute_option_group',
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Option',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False)),
                ('label', models.CharField(max_length=128, verbose_name='Label')),
                ('identifier', models.SlugField(help_text='Identifier used for looking up conditional.', max_length=128, unique=True, validators=[django.core.validators.RegexValidator(message="Identifier only contain the letters a-z, A-Z, digits, and underscores, and can't start with a digit.", regex='^[a-zA-Z_][0-9a-zA-Z_]*$')], verbose_name='Identifier')),
                ('required', models.PositiveIntegerField(choices=[(1, 'Required - a value for this option must be specified'), (0, 'Optional - a value for this option can be omitted')], default=1, verbose_name='Status')),
            ],
            options={
                'verbose_name': 'Option',
                'verbose_name_plural': 'Options',
                'db_table': 'person_option',
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Role',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False)),
                ('label', models.CharField(max_length=255)),
                ('identifier', models.SlugField(help_text='Identifier used for looking up conditional.', max_length=168, unique=True, validators=[django.core.validators.RegexValidator(message="Identifier only contain the letters a-z, A-Z, digits, and underscores, and can't start with a digit.", regex='^[a-zA-Z_][0-9a-zA-Z_]*$')], verbose_name='Identifier')),
                ('date_created', models.DateTimeField(auto_now_add=True)),
                ('date_updated', models.DateTimeField(auto_now=True)),
                ('is_active', models.BooleanField(default=True)),
                ('is_default', models.BooleanField(default=False, null=True)),
            ],
            options={
                'verbose_name': 'Role',
                'verbose_name_plural': 'Roles',
                'db_table': 'person_role',
                'abstract': False,
                'unique_together': {('identifier', 'is_default')},
            },
        ),
        migrations.CreateModel(
            name='Person',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('options', models.ManyToManyField(blank=True, to='person.Option', verbose_name='Options')),
                ('roles', models.ManyToManyField(related_name='roles', to='person.Role')),
                ('user', models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='person', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Person',
                'verbose_name_plural': 'Persons',
                'db_table': 'person',
                'ordering': ['-user__date_joined'],
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='AttributeOption',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False)),
                ('option', models.CharField(max_length=255, verbose_name='Option')),
                ('group', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='options', to='person.AttributeOptionGroup', verbose_name='Group')),
            ],
            options={
                'verbose_name': 'Attribute option',
                'verbose_name_plural': 'Attribute options',
                'db_table': 'person_attribute_option',
                'abstract': False,
                'unique_together': {('group', 'option')},
            },
        ),
        migrations.CreateModel(
            name='Attribute',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False)),
                ('label', models.CharField(max_length=128, verbose_name='Label')),
                ('identifier', models.SlugField(max_length=128, validators=[django.core.validators.RegexValidator(message="Code can only contain the letters a-z, A-Z, digits, and underscores, and can't start with a digit.", regex='^[a-zA-Z_][0-9a-zA-Z_]*$'), utils.validators.non_python_keyword], verbose_name='Identifier')),
                ('type', models.CharField(choices=[('text', 'Text'), ('url', 'URL'), ('integer', 'Integer'), ('boolean', 'True / False'), ('float', 'Float'), ('richtext', 'Rich Text'), ('date', 'Date'), ('datetime', 'Datetime'), ('option', 'Option'), ('multi_option', 'Multi Option'), ('entity', 'Entity'), ('file', 'File'), ('image', 'Image')], default='text', max_length=20, verbose_name='Type')),
                ('required', models.BooleanField(default=False, verbose_name='Required')),
                ('option_group', models.ForeignKey(blank=True, help_text='Select option group if using type "Option" or "Multi Option"', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='person_attributes', to='person.AttributeOptionGroup', verbose_name='Option Group')),
                ('roles', models.ManyToManyField(blank=True, help_text='Limit attributes by Roles.', limit_choices_to=models.Q(is_active=True), to='person.Role')),
            ],
            options={
                'verbose_name': 'Attribute',
                'verbose_name_plural': 'Attributes',
                'db_table': 'person_attribute',
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='AttributeValue',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False)),
                ('value_text', models.CharField(blank=True, max_length=255, null=True, verbose_name='Text')),
                ('value_url', models.URLField(blank=True, max_length=500, null=True, verbose_name='URL')),
                ('value_integer', models.IntegerField(blank=True, db_index=True, null=True, verbose_name='Integer')),
                ('value_boolean', models.NullBooleanField(db_index=True, verbose_name='Boolean')),
                ('value_float', models.FloatField(blank=True, db_index=True, null=True, verbose_name='Float')),
                ('value_richtext', models.TextField(blank=True, null=True, verbose_name='Richtext')),
                ('value_date', models.DateField(blank=True, db_index=True, null=True, verbose_name='Date')),
                ('value_datetime', models.DateTimeField(blank=True, db_index=True, null=True, verbose_name='DateTime')),
                ('value_file', models.FileField(blank=True, max_length=255, null=True, upload_to=apps.person.models.models_attribute.entity_directory_file_path)),
                ('value_image', models.ImageField(blank=True, max_length=255, null=True, upload_to=apps.person.models.models_attribute.entity_directory_image_path)),
                ('entity_id', models.PositiveIntegerField(blank=True, editable=False, null=True)),
                ('attribute', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='person.Attribute', verbose_name='Attribute')),
                ('entity_content_type', models.ForeignKey(blank=True, editable=False, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='person_attribute_value_entity', to='contenttypes.ContentType')),
                ('person', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='attribute_values', to='person.Person', verbose_name='Person')),
                ('value_multi_option', models.ManyToManyField(blank=True, related_name='multi_valued_attribute_values', to='person.AttributeOption', verbose_name='Value multi option')),
                ('value_option', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='person.AttributeOption', verbose_name='Value option')),
            ],
            options={
                'verbose_name': 'Person attribute value',
                'verbose_name_plural': 'Person attribute values',
                'db_table': 'person_attribute_value',
                'abstract': False,
                'unique_together': {('attribute', 'person')},
            },
        ),
    ]
