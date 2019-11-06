# Generated by Django 2.2.6 on 2019-10-31 11:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('person', '0007_validation_validationvalue'),
    ]

    operations = [
        migrations.AddField(
            model_name='attribute',
            name='instruction',
            field=models.TextField(blank=True, null=True, verbose_name='Instruction'),
        ),
        migrations.AddField(
            model_name='attributevalue',
            name='value_email',
            field=models.EmailField(blank=True, max_length=255, null=True, verbose_name='Email'),
        ),
        migrations.AddField(
            model_name='validation',
            name='instruction',
            field=models.TextField(blank=True, verbose_name='Instruction'),
        ),
        migrations.AddField(
            model_name='validationvalue',
            name='secure_code',
            field=models.CharField(max_length=128, null=True),
        ),
        migrations.AddField(
            model_name='validationvalue',
            name='value_email',
            field=models.EmailField(blank=True, max_length=255, null=True, verbose_name='Email'),
        ),
        migrations.AlterField(
            model_name='attribute',
            name='field_type',
            field=models.CharField(choices=[('text', 'Text'), ('email', 'Email'), ('url', 'URL'), ('integer', 'Integer'), ('boolean', 'True / False'), ('float', 'Float'), ('richtext', 'Rich Text'), ('date', 'Date'), ('datetime', 'Datetime'), ('option', 'Option'), ('multi_option', 'Multi Option'), ('file', 'File'), ('image', 'Image')], default='text', max_length=20, verbose_name='Type'),
        ),
        migrations.AlterField(
            model_name='validation',
            name='field_type',
            field=models.CharField(choices=[('text', 'Text'), ('email', 'Email'), ('url', 'URL'), ('integer', 'Integer'), ('richtext', 'Rich Text'), ('file', 'File'), ('image', 'Image')], default='text', max_length=20, verbose_name='Type'),
        ),
    ]
