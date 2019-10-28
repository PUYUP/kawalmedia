import uuid
import datetime

from django.conf import settings
from django.db import models
from django.db.models import Q
from django.contrib.contenttypes.fields import (
    GenericForeignKey, GenericRelation)
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import ugettext_lazy as _
from django.core.validators import RegexValidator
from django.template.defaultfilters import slugify

from ..utils.generals import (
    find_parent_key,
    find_value_with_key,
    tuple_to_dict,
    FileSystemStorageExtend)

from ..utils.constant import (
    STATUS_CHOICES, SCORE_CHOICES, PURPOSE_CHOICES,
    CLASSIFICATION_CHOICES, PUBLICATION_CHOICES)


def directory_image_path(instance, filename):
    fs = FileSystemStorageExtend()
    year = datetime.date.today().year
    month = datetime.date.today().month
    content_type_slug = slugify(instance.content_type)
    filename = fs.generate_filename(filename, instance=instance)

    # Will be 'files/2019/10/filename.jpg
    return 'images/{0}/{1}/{2}'.format(year, month, filename)


def directory_file_path(instance, filename):
    fs = FileSystemStorageExtend()
    year = datetime.date.today().year
    month = datetime.date.today().month
    content_type_slug = slugify(instance.content_type)
    filename = fs.generate_filename(filename, instance=instance)

    # Will be 'files/2019/10/filename.jpg
    return 'files/{0}/{1}/{2}'.format(year, month, filename)


class AbstractMedia(models.Model):
    """Basic of media..."""
    creator = models.ForeignKey(
        'person.Person',
        on_delete=models.CASCADE,
        null=True, blank=True,
        related_name='creator')
    options = models.ManyToManyField(
        'escort.Option', blank=True, verbose_name=_("Options"))
    classification = models.PositiveIntegerField(
        choices=CLASSIFICATION_CHOICES)
    publication = models.PositiveIntegerField(
        choices=PUBLICATION_CHOICES)

    # Generic relations
    attribute_values = GenericRelation(
        'escort.AttributeValue',
        related_query_name='media')
    status_log = GenericRelation(
        'escort.EntityLog',
        related_query_name='status_log')
    attachments = GenericRelation(
        'escort.Attachment',
        related_query_name='media_attachment')

    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    label = models.CharField(max_length=255)
    status = models.PositiveIntegerField(choices=STATUS_CHOICES, default=1)
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)

    # Increments store
    protest_count = models.PositiveIntegerField(editable=False, default=0)
    comment_count = models.PositiveIntegerField(editable=False, default=0)
    rating_count = models.PositiveIntegerField(editable=False, default=0)

    class Meta:
        abstract = True
        app_label = 'escort'
        unique_together = ['label']
        ordering = ['-date_created']
        verbose_name = _('Media')
        verbose_name_plural = _('Medias')

    def __str__(self):
        return self.label

    def save(self, *args, **kwargs):
        # Auto fill classification by select publication
        publication = self.publication
        if publication:
            # Get label
            # Ex: ('name', 'Name')
            # Return 'Name'
            value_verbose = find_value_with_key(
                publication, PUBLICATION_CHOICES)

            # Get key tuple
            # Return ('value', 'Value')
            classification_key = find_parent_key(
                tuple_to_dict(PUBLICATION_CHOICES), value_verbose)

            # Then set classification value
            self.classification = classification_key[0]
        super().save(*args, **kwargs)


class AbstractResponsible(models.Model):
    """Mapping Media with it's Responsible"""
    media = models.ForeignKey(
        'escort.Media',
        limit_choices_to={'status': 3},
        on_delete=models.CASCADE,
        verbose_name=_("Media"))
    responser = models.ForeignKey(
        'person.Person',
        on_delete=models.CASCADE,
        null=True, related_name='responser')
    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    label = models.CharField(max_length=255)
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
        app_label = 'escort'
        unique_together = ['media', 'responser']
        ordering = ['-date_created']
        verbose_name = _('Responsible')
        verbose_name_plural = _('Responsibles')

    def __str__(self):
        return self.responser.user.username


class AbstractRating(models.Model):
    media = models.ForeignKey(
        'escort.Media',
        limit_choices_to={'status': 3},
        on_delete=models.CASCADE,
        verbose_name=_("Media"))
    rater = models.ForeignKey(
        'person.Person',
        on_delete=models.SET_NULL,
        null=True, related_name='rater')
    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    score = models.PositiveIntegerField(choices=SCORE_CHOICES)
    description = models.TextField(_('Description'), blank=True)
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
        app_label = 'escort'
        unique_together = ['media', 'rater']
        ordering = ['-date_updated']
        verbose_name = _('Rating')
        verbose_name_plural = _('Ratings')

    def __str__(self):
        return self.media.label


class AbstractOption(models.Model):
    """
    An option for user
    Example is user validate email? Or validate phone? Or other...
    """
    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    label = models.CharField(_("Label"), max_length=128)
    identifier = models.SlugField(
        _('Identifier'), max_length=128, unique=True,
        validators=[
            RegexValidator(
                regex=r'^[a-zA-Z_][0-9a-zA-Z_]*$',
                message=_(
                    "Identifier only contain the letters a-z, A-Z, digits, "
                    "and underscores, and can't start with a digit."))],
        help_text=_("Identifier used for looking up conditional."))

    REQUIRED, OPTIONAL = (1, 0)
    TYPE_CHOICES = (
        (REQUIRED, _("Required - a value for this option must be specified")),
        (OPTIONAL, _("Optional - a value for this option can be omitted")),
    )
    required = models.PositiveIntegerField(
        _("Status"), default=REQUIRED, choices=TYPE_CHOICES)

    class Meta:
        abstract = True
        app_label = 'escort'
        verbose_name = _("Option")
        verbose_name_plural = _("Options")

    def __str__(self):
        return self.label

    @property
    def is_required(self):
        return self.required == self.REQUIRED


class AbstractAttachment(models.Model):
    """General attachment used for various objects"""
    uploader = models.ForeignKey(
        'person.Person',
        on_delete=models.SET_NULL,
        null=True, related_name='uploader')
    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    value_image = models.ImageField(
        upload_to=directory_image_path,
        max_length=500, null=True, blank=True)
    value_file = models.FileField(
        upload_to=directory_file_path,
        max_length=500, null=True, blank=True)
    featured = models.BooleanField(null=True)
    caption = models.TextField(max_length=500, null=True, blank=True)
    date_created = models.DateTimeField(auto_now_add=True, null=True)
    date_updated = models.DateTimeField(auto_now=True, null=True)

    # Generic relations
    content_type = models.ForeignKey(
        ContentType, on_delete=models.CASCADE,
        related_name='escort_entity_attachment',
        limit_choices_to=Q(app_label='escort'))
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

    class Meta:
        abstract = True
        app_label = 'escort'
        ordering = ['-date_updated']
        verbose_name = _('Attachment')
        verbose_name_plural = _('Attachments')

    def __str__(self):
        value = ''
        if self.value_image:
            value = self.value_image.url

        if self.value_file:
            value = self.value_file.url
        return value


class AbstractProtest(models.Model):
    """Person protest a media"""
    protester = models.ForeignKey(
        'person.Person',
        on_delete=models.SET_NULL,
        null=True, related_name='protester')
    media = models.ForeignKey(
        'escort.Media',
        limit_choices_to={'status': 3},
        on_delete=models.CASCADE,
        verbose_name=_("Media"))
    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    label = models.CharField(max_length=255)
    description = models.TextField()
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)
    status = models.PositiveIntegerField(choices=STATUS_CHOICES, default=1)
    status_log = GenericRelation(
        'escort.EntityLog',
        related_query_name='status_log')
    purpose = models.PositiveIntegerField(choices=PURPOSE_CHOICES, default=3)

    attachments = GenericRelation(
        'escort.Attachment',
        related_query_name='protest_attachment')

    thumbs = GenericRelation(
        'escort.Thumbed',
        related_query_name='protest_thumb')

    # Increments store
    thumbsup_count = models.PositiveIntegerField(
        editable=False, default=0)
    thumbsdown_count = models.PositiveIntegerField(
        editable=False, default=0)
    comment_count = models.PositiveIntegerField(
        editable=False, default=0)

    class Meta:
        abstract = True
        app_label = 'escort'
        ordering = ['-date_updated']
        verbose_name = _('Protest')
        verbose_name_plural = _('Protests')

    def __str__(self):
        return self.label


class AbstractEntityLog(models.Model):
    """Log all entity if needed"""
    logger = models.ForeignKey(
        'person.Person',
        on_delete=models.SET_NULL,
        null=True, related_name='logger')
    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    status = models.PositiveIntegerField(choices=STATUS_CHOICES, default=1)
    description = models.TextField(null=True, blank=True)
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)

    # Generic foreignkey
    content_type = models.ForeignKey(
        ContentType, on_delete=models.CASCADE, null=True,
        related_name='escort_entity_attibutes',
        limit_choices_to=Q(app_label='escort'))
    object_id = models.PositiveIntegerField(null=True)
    content_object = GenericForeignKey('content_type', 'object_id')

    class Meta:
        abstract = True
        app_label = 'escort'
        verbose_name = _('Entity log')
        verbose_name_plural = _('Entity log')

    def __str__(self):
        label = getattr(self.content_object, 'label', None)
        if not label:
            label = getattr(self.content_object, 'user', None)
        return label


class AbstractComment(models.Model):
    """Mapping protest and their comment"""
    protest = models.ForeignKey(
        'escort.Protest',
        on_delete=models.CASCADE,
        verbose_name=_("Protest"))
    commenter = models.ForeignKey(
        'person.Person',
        on_delete=models.SET_NULL,
        null=True, related_name='commenter')

    parent = models.ForeignKey(
        'self',
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name='children',
        verbose_name=_("Parent comment"))
    reply_to_comment = models.ForeignKey(
        'self',
        blank=True,
        null=True,
        on_delete=models.CASCADE,
        related_name='reply_to',
        verbose_name=_("Reply yo comment"))
    reply_for_person = models.ForeignKey(
        'person.Person',
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name='reply_for')

    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    description = models.TextField()
    reply_count = models.PositiveIntegerField(
        editable=False, default=0)
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)

    attachments = GenericRelation(
        'escort.Attachment',
        related_query_name='comment_attachment')

    thumbs = GenericRelation(
        'escort.Thumbed',
        related_query_name='comment_thumb')

    class Meta:
        abstract = True
        app_label = 'escort'
        ordering = ('-date_created',)
        verbose_name = _('Comment')
        verbose_name_plural = _('Comments')

    def __str__(self):
        return self.protest.label


class AbstractThumbed(models.Model):
    """Each person add thumb up or down capture it"""
    thumber = models.ForeignKey(
        'person.Person',
        on_delete=models.SET_NULL,
        null=True, related_name='thumber')
    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    thumbing = models.NullBooleanField(null=True)
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)

    # Generic foreignkey
    content_type = models.ForeignKey(
        ContentType, on_delete=models.CASCADE,
        related_name='escort_thumbed',
        limit_choices_to=Q(app_label='escort'))
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

    class Meta:
        abstract = True
        app_label = 'escort'
        unique_together = ('thumber', 'content_type', 'object_id')
        verbose_name = _('Thumbed')
        verbose_name_plural = _('Thumbeds')

    def __str__(self):
        return self.thumber.user.username
