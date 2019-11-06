import os
import uuid

from django.conf import settings
from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.core.validators import RegexValidator
from django.utils.html import strip_tags
from django.utils.safestring import mark_safe
from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from django.utils.text import slugify

# PROJECTS UTILS
from utils.validators import non_python_keyword, get_model

# LOCAL UTILS
from ..utils.constant import FIELD_TYPE_CHOICES


def entity_directory_image_path(instance, filename):
    # file will be uploaded to MEDIA_ROOT/images/<entity>_<id>/<filename>
    object_id = instance.object_id
    ct = ContentType.objects.get_for_id(instance.content_type.pk)
    obj = ct.get_object_for_this_type(pk=object_id)

    model_class = instance.content_type.model_class()
    model_name = slugify(model_class._meta.model_name)
    model_uuid = obj.uuid
    return 'images/{0}_{1}/{2}'.format(model_name, model_uuid, filename)


def entity_directory_file_path(instance, filename):
    # file will be uploaded to MEDIA_ROOT/files/<entity>_<id>/<filename>
    object_id = instance.object_id
    ct = ContentType.objects.get_for_id(instance.content_type.pk)
    obj = ct.get_object_for_this_type(pk=object_id)

    model_class = instance.content_type.model_class()
    model_name = slugify(model_class._meta.model_name)
    model_uuid = obj.uuid
    return 'files/{0}_{1}/{2}'.format(model_name, model_uuid, filename)


# Create your models here.
class AbstractAttribute(models.Model):
    """
    Attribute for entity filter by content_type
    """
    roles = models.ManyToManyField(
        'person.Role',
        blank=True,
        limit_choices_to=Q(is_active=True),
        help_text=_("Limit attributes by Roles."))
    content_type = models.ManyToManyField(
        ContentType, blank=True, related_name='person_attibute',
        limit_choices_to=Q(app_label='person'))
    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    label = models.CharField(_('Label'), max_length=128)
    identifier = models.SlugField(
        _('Identifier'), max_length=128,
        validators=[
            RegexValidator(
                regex=r'^[a-zA-Z_][0-9a-zA-Z_]*$',
                message=_(
                    "Code can only contain the letters a-z, A-Z, digits, "
                    "and underscores, and can't start with a digit.")),
            non_python_keyword
        ])
    field_type = models.CharField(
        choices=FIELD_TYPE_CHOICES,
        default=FIELD_TYPE_CHOICES[0][0],
        max_length=20, verbose_name=_("Type"))
    option_group = models.ForeignKey(
        'person.AttributeOptionGroup',
        blank=True,
        null=True,
        on_delete=models.CASCADE,
        related_name='content_attributes',
        verbose_name=_("Option Group"),
        help_text=_('Select option group if using '
                    'type "Option" or "Multi Option"'))
    instruction = models.TextField(_('Instruction'), blank=True, null=True)
    placeholder = models.CharField(max_length=255, blank=True, null=True)
    secured = models.BooleanField(_('Secured'), default=False)
    required = models.BooleanField(_('Required'), default=False)

    class Meta:
        abstract = True
        app_label = 'person'
        verbose_name = _('Attribute')
        verbose_name_plural = _('Attributes')

    def __str__(self):
        return self.label

    @property
    def is_option(self):
        if hasattr(self, 'OPTION'):
            return self.field_type == self.OPTION
        pass

    @property
    def is_multi_option(self):
        if hasattr(self, 'MULTI_OPTION'):
            return self.field_type == self.MULTI_OPTION
        pass

    @property
    def is_file(self):
        if hasattr(self, 'FILE') or hasattr(self, 'IMAGE'):
            return self.field_type in [self.FILE, self.IMAGE]
        pass

    def _save_file(self, value_obj, value):
        # File fields in Django are treated differently, see
        # django.db.models.fields.FileField and method save_form_data
        if value is None:
            # No change
            return
        elif value is False:
            # Delete file
            value_obj.delete()
        else:
            # New uploaded file
            value_obj.value = value
            value_obj.save()

    def _save_multi_option(self, value_obj, value):
        # ManyToMany fields are handled separately
        if value is None:
            value_obj.delete()
            return
        try:
            count = value.count()
        except (AttributeError, TypeError):
            count = len(value)
        if count == 0:
            value_obj.delete()
        else:
            value_obj.value = value
            value_obj.save()

    def _save_value(self, value_obj, value):
        if value is None or value == '':
            value_obj.delete()
            return
        if value != value_obj.value:
            value_obj.value = value
            value_obj.save()

    def save_value(self, entity, value):   # noqa: C901 too complex
        AttributeValue = get_model('person', 'AttributeValue')
        try:
            value_obj = AttributeValue.get(
                attribute=self, content_object=entity)
        except AttributeValue.DoesNotExist:
            # FileField uses False for announcing deletion of the file
            # not creating a new value
            delete_file = self.is_file and value is False
            if value is None or value == '' or delete_file:
                return
            value_obj = AttributeValue.objects.create(
                content_object=entity, attribute=self)

        if self.is_file:
            self._save_file(value_obj, value)
        elif self.is_multi_option:
            self._save_multi_option(value_obj, value)
        else:
            self._save_value(value_obj, value)

    def validate_value(self, value):
        validator = getattr(self, '_validate_%s' % self.field_type)
        validator(value)

    # Validators

    def _validate_text(self, value):
        if not isinstance(value, str):
            raise ValidationError(_("Must be str"))
    _validate_richtext = _validate_text

    def _validate_float(self, value):
        try:
            float(value)
        except ValueError:
            raise ValidationError(_("Must be a float"))

    def _validate_integer(self, value):
        try:
            int(value)
        except ValueError:
            raise ValidationError(_("Must be an integer"))

    def _validate_date(self, value):
        if not (isinstance(value, datetime) or isinstance(value, date)):
            raise ValidationError(_("Must be a date or datetime"))

    def _validate_datetime(self, value):
        if not isinstance(value, datetime):
            raise ValidationError(_("Must be a datetime"))

    def _validate_boolean(self, value):
        if not type(value) == bool:
            raise ValidationError(_("Must be a boolean"))

    def _validate_multi_option(self, value):
        try:
            values = iter(value)
        except TypeError:
            raise ValidationError(
                _("Must be a list or AttributeOption queryset"))
        # Validate each value as if it were an option
        # Pass in valid_values so that the DB
        # isn't hit multiple times per iteration
        valid_values = self.option_group.options.values_list(
            'option', flat=True)
        for value in values:
            self._validate_option(value, valid_values=valid_values)

    def _validate_option(self, value, valid_values=None):
        if not isinstance(value, get_model('person', 'AttributeOption')):
            raise ValidationError(
                _("Must be an AttributeOption model object instance"))
        if not value.pk:
            raise ValidationError(_("AttributeOption has not been saved yet"))
        if valid_values is None:
            valid_values = self.option_group.options.values_list(
                'option', flat=True)
        if value.option not in valid_values:
            raise ValidationError(
                _("%(enum)s is not a valid choice for %(attr)s") %
                {'enum': value, 'attr': self})

    def _validate_file(self, value):
        if value and not isinstance(value, File):
            raise ValidationError(_("Must be a file field"))
    _validate_image = _validate_file


class AbstractAttributeValue(models.Model):
    """Mapping value with entity"""
    attribute = models.ForeignKey(
        'person.Attribute',
        on_delete=models.CASCADE,
        verbose_name=_("Attribute"))
    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    value_text = models.CharField(
        _('Text'), blank=True, null=True, max_length=255)
    value_email = models.EmailField(
        _('Email'), blank=True, null=True, max_length=255)
    value_url = models.URLField(
        _('URL'), blank=True, null=True, max_length=500)
    value_integer = models.IntegerField(
        _('Integer'), blank=True, null=True, db_index=True)
    value_boolean = models.NullBooleanField(
        _('Boolean'), blank=True, db_index=True)
    value_float = models.FloatField(
        _('Float'), blank=True, null=True, db_index=True)
    value_richtext = models.TextField(_('Richtext'), blank=True, null=True)
    value_date = models.DateField(
        _('Date'), blank=True, null=True, db_index=True)
    value_datetime = models.DateTimeField(
        _('DateTime'), blank=True, null=True, db_index=True)
    value_multi_option = models.ManyToManyField(
        'person.AttributeOption',
        blank=True,
        related_name='multi_valued_attribute_values',
        verbose_name=_("Value multi option"))
    value_option = models.ForeignKey(
        'person.AttributeOption',
        blank=True,
        null=True,
        on_delete=models.CASCADE,
        verbose_name=_("Value option"))
    value_file = models.FileField(
        upload_to=entity_directory_file_path, max_length=255,
        blank=True, null=True)
    value_image = models.ImageField(
        upload_to=entity_directory_image_path, max_length=255,
        blank=True, null=True)

    date_created = models.DateTimeField(auto_now_add=True, null=True)
    date_updated = models.DateTimeField(auto_now=True, null=True)

    # Generic foreignkey
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        blank=True, null=True,
        related_name='person_entity_attibutes',
        limit_choices_to=Q(app_label='person'))
    object_id = models.PositiveIntegerField(
        null=True, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')

    def _get_value(self):
        value = getattr(self, 'value_%s' % self.attribute.field_type)
        if hasattr(value, 'all'):
            value = value.all()
        return value

    def _set_value(self, new_value):
        attr_label = 'value_%s' % self.attribute.field_type

        if self.attribute.is_option and isinstance(new_value, str):
            # Need to look up instance of AttributeOption
            new_value = self.attribute.option_group.options.get(
                option=new_value)
        elif self.attribute.is_multi_option:
            getattr(self, attr_label).set(new_value)
            return

        setattr(self, attr_label, new_value)
        return

    value = property(_get_value, _set_value)

    class Meta:
        abstract = True
        app_label = 'person'
        unique_together = ('attribute', 'content_type', 'object_id')
        verbose_name = _('Attribute value')
        verbose_name_plural = _('Attribute values')

    def __str__(self):
        return self.summary()

    def summary(self):
        """
        Gets a string representation of both the attribute and it's value,
        used e.g in entity summaries.
        """
        return "%s: %s" % (self.attribute.label, self.value_as_text)

    @property
    def value_as_text(self):
        """
        Returns a string representation of the attribute's value. To customise
        e.g. image attribute values, declare a _image_as_text property and
        return something appropriate.
        """
        property_label = '_%s_as_text' % self.attribute.field_type
        return getattr(self, property_label, self.value)

    @property
    def _multi_option_as_text(self):
        return ', '.join(
            str(option) for option in self.value_multi_option.all())

    @property
    def _option_as_text(self):
        return str(self.value_option)

    @property
    def _richtext_as_text(self):
        return strip_tags(self.value)

    @property
    def value_as_html(self):
        """
        Returns a HTML representation of the attribute's value. To customise
        e.g. image attribute values, declare a _image_as_html property and
        return e.g. an <img> tag.  Defaults to the _as_text representation.
        """
        property_label = '_%s_as_html' % self.attribute.field_type
        return getattr(self, property_label, self.value_as_text)

    @property
    def _richtext_as_html(self):
        return mark_safe(self.value)


class AbstractAttributeOptionGroup(models.Model):
    """
    Defines a group of options that collectively may be used as an
    attribute type

    For example, Language
    """
    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    label = models.CharField(_('Label'), max_length=128)
    identifier = models.SlugField(
        _('Identifier'), max_length=128, null=True,
        validators=[
            RegexValidator(
                regex=r'^[a-zA-Z_][0-9a-zA-Z_]*$',
                message=_(
                    "Code can only contain the letters a-z, A-Z, digits, "
                    "and underscores, and can't start with a digit.")),
            non_python_keyword
        ])

    def __str__(self):
        return self.label

    class Meta:
        abstract = True
        app_label = 'person'
        verbose_name = _('Attribute option group')
        verbose_name_plural = _('Attribute option groups')

    @property
    def option_summary(self):
        options = [o.option for o in self.options.all()]
        return ", ".join(options)


class AbstractAttributeOption(models.Model):
    """
    Provides an option within an option group for an attribute type
    Examples: In a Language group, English, Greek, French
    """
    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    group = models.ForeignKey(
        'person.AttributeOptionGroup',
        on_delete=models.CASCADE,
        related_name='options',
        verbose_name=_("Group"))
    option = models.CharField(_('Option'), max_length=255)

    class Meta:
        abstract = True
        app_label = 'person'
        unique_together = ('group', 'option')
        verbose_name = _('Attribute option')
        verbose_name_plural = _('Attribute options')

    def __str__(self):
        return self.option
