import uuid

from django.conf import settings
from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import ugettext_lazy as _
from django.core.validators import RegexValidator
from django.db.models import Q

# PROJECTS UTILS
from utils.validators import non_python_keyword, get_model

# LOCAL UTILS
from ..utils.constant import FIELD_VALIDATION_CHOICES, VERIFICATION_METHOD


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


class AbstractValidation(models.Model):
    """Validation for entity filter by content_type"""
    roles = models.ManyToManyField(
        'person.Role',
        blank=True,
        limit_choices_to=Q(is_active=True),
        help_text=_("Limit validations by Roles."))
    content_type = models.ManyToManyField(
        ContentType, blank=True, related_name='person_validation',
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
        choices=FIELD_VALIDATION_CHOICES,
        default=FIELD_VALIDATION_CHOICES[0][0],
        max_length=20, verbose_name=_("Type"))
    instruction = models.TextField(_('Instruction'), blank=True)
    placeholder = models.CharField(max_length=255, blank=True, null=True)
    secured = models.BooleanField(_('Secured'), default=False)
    required = models.BooleanField(_('Required'), default=False)
    method = models.IntegerField(
        choices=VERIFICATION_METHOD, null=True,
        help_text=_("Verification method"))

    class Meta:
        abstract = True
        app_label = 'person'
        verbose_name = _('Validation')
        verbose_name_plural = _('Validations')

    def __str__(self):
        return self.label

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

    def _save_value(self, value_obj, value):
        if value is None or value == '':
            value_obj.delete()
            return
        if value != value_obj.value:
            value_obj.value = value
            value_obj.save()

    def save_value(self, entity, value):   # noqa: C901 too complex
        ValidationValue = get_model('person', 'ValidationValue')
        try:
            value_obj = ValidationValue.get(
                validation=self, content_object=entity)
        except ValidationValue.DoesNotExist:
            # FileField uses False for announcing deletion of the file
            # not creating a new value
            delete_file = self.is_file and value is False
            if value is None or value == '' or delete_file:
                return
            value_obj = ValidationValue.objects.create(
                content_object=entity, validation=self)

        if self.is_file:
            self._save_file(value_obj, value)
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

    def _validate_integer(self, value):
        try:
            int(value)
        except ValueError:
            raise ValidationError(_("Must be an integer"))

    def _validate_file(self, value):
        if value and not isinstance(value, File):
            raise ValidationError(_("Must be a file field"))
    _validate_image = _validate_file


class AbstractValidationValue(models.Model):
    """Mapping value with entity"""
    validation = models.ForeignKey(
        'person.Validation',
        on_delete=models.CASCADE,
        verbose_name=_("Validation"))
    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    secure_code = models.CharField(max_length=128, null=True, blank=True)
    verified = models.BooleanField(null=True)
    value_text = models.CharField(
        _('Text'), blank=True, null=True, max_length=255)
    value_email = models.EmailField(
        _('Email'), blank=True, null=True, max_length=255)
    value_url = models.URLField(
        _('URL'), blank=True, null=True, max_length=500)
    value_integer = models.IntegerField(
        _('Integer'), blank=True, null=True, db_index=True)
    value_richtext = models.TextField(_('Richtext'), blank=True, null=True)
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
        related_name='person_entity_validation',
        limit_choices_to=Q(app_label='person'))
    object_id = models.PositiveIntegerField(
        null=True, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')

    def _get_value(self):
        value = getattr(self, 'value_%s' % self.validation.field_type)
        if hasattr(value, 'all'):
            value = value.all()
        return value

    def _set_value(self, new_value):
        attr_label = 'value_%s' % self.validation.field_type
        setattr(self, attr_label, new_value)
        return

    value = property(_get_value, _set_value)

    class Meta:
        abstract = True
        app_label = 'person'
        unique_together = ('validation', 'content_type', 'object_id')
        verbose_name = _('Validation value')
        verbose_name_plural = _('Validation values')

    def __str__(self):
        return self.summary()

    def summary(self):
        """
        Gets a string representation of both the validation and it's value,
        used e.g in entity summaries.
        """
        return "%s: %s" % (self.validation.label, self.value_as_text)

    @property
    def value_as_text(self):
        """
        Returns a string representation of the validation's value. To customise
        e.g. image validation values, declare a _image_as_text property and
        return something appropriate.
        """
        property_label = '_%s_as_text' % self.validation.field_type
        return getattr(self, property_label, self.value)

    @property
    def _richtext_as_text(self):
        return strip_tags(self.value)

    @property
    def value_as_html(self):
        """
        Returns a HTML representation of the validation's value. To customise
        e.g. image validation values, declare a _image_as_html property and
        return e.g. an <img> tag.  Defaults to the _as_text representation.
        """
        property_label = '_%s_as_html' % self.validation.field_type
        return getattr(self, property_label, self.value_as_text)

    @property
    def _richtext_as_html(self):
        return mark_safe(self.value)
