import uuid
import datetime

from django.db import models
from django.db.models import Q
from django.contrib.contenttypes.fields import (
    GenericForeignKey, GenericRelation)
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import ugettext_lazy as _
from django.template.defaultfilters import slugify

# Other apps UTILS
from ..utils.constant import STATUS_CHOICES
from ..utils.generals import FileSystemStorageExtend


def directory_image_path(instance, filename):
    fs = FileSystemStorageExtend()
    year = datetime.date.today().year
    month = datetime.date.today().month
    content_type_slug = slugify(instance.content_type)
    filename = fs.generate_filename(filename, instance=instance)

    # Will be 'images/2019/10/filename.jpg
    return 'images/{0}/{1}/{2}'.format(year, month, filename)


def directory_file_path(instance, filename):
    fs = FileSystemStorageExtend()
    year = datetime.date.today().year
    month = datetime.date.today().month
    content_type_slug = slugify(instance.content_type)
    filename = fs.generate_filename(filename, instance=instance)

    # Will be 'files/2019/10/filename.jpg
    return 'files/{0}/{1}/{2}'.format(year, month, filename)


class AbstractArticle(models.Model):
    """Basic of article..."""
    writer = models.ForeignKey(
        'person.Person',
        on_delete=models.CASCADE,
        null=True, blank=True,
        related_name='writer')

    attachments = GenericRelation(
        'knowledgebase.Attachment',
        related_query_name='article_attachment')

    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    label = models.CharField(max_length=255)
    icon = models.CharField(max_length=255, null=True, blank=True)
    description = models.TextField(_('Description'), blank=True)
    status = models.PositiveIntegerField(choices=STATUS_CHOICES, default=1)
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
        app_label = 'knowledgebase'
        unique_together = ['label']
        ordering = ['-date_created']
        verbose_name = _('Article')
        verbose_name_plural = _('Articles')

    def __str__(self):
        return self.label


class AbstractAttachment(models.Model):
    """General attachment used for various objects"""
    uploader = models.ForeignKey(
        'person.Person',
        on_delete=models.SET_NULL,
        null=True, related_name='knowledgebase_uploader')
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
        related_name='knowledgebase_entity_attachment',
        limit_choices_to=Q(app_label='knowledgebase'))
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

    class Meta:
        abstract = True
        app_label = 'knowledgebase'
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
