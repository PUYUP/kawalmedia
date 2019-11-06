import uuid

from django.db import models
from django.db.models import Q
from django.contrib.contenttypes.fields import (
    GenericForeignKey, GenericRelation)
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import ugettext_lazy as _
from django.utils.text import slugify


class NotificationQuerySet(models.query.QuerySet):
    """Personalized queryset created to improve model usability"""

    def unread(self):
        """Return only unread items in the current queryset"""
        return self.filter(unread=True)

    def read(self):
        """Return only read items in the current queryset"""
        return self.filter(unread=False)

    def mark_all_as_read(self, recipient=None):
        """Mark as read any unread elements in the current queryset with
        optional filter by recipient first.
        """
        qs = self.unread()
        if recipient:
            qs = qs.filter(recipient=recipient)

        return qs.update(unread=False)

    def mark_all_as_unread(self, recipient=None):
        """Mark as unread any read elements in the current queryset with
        optional filter by recipient first.
        """
        qs = self.read()
        if recipient:
            qs = qs.filter(recipient=recipient)

        return qs.update(unread=True)

    def get_most_recent(self, recipient=None):
        """Returns the most recent unread elements in the queryset"""
        qs = self.unread()[:5]
        if recipient:
            qs = qs.filter(recipient=recipient)[:5]

        return qs


class AbstractNotification(models.Model):
    """
    Action model describing the actor acting out a verb (on an optional target).
    Nomenclature based on http://activitystrea.ms/specs/atom/1.0/
    This model is an adaptation from the django package django-notifications at
    https://github.com/django-notifications/django-notifications
    Generalized Format::
        <actor> <verb> <time>
        <actor> <verb> <action_object> <time>
    Examples::
        <Sebastian> <Logged In> <1 minute ago>
        <Sebastian> <commented> <Article> <2 hours ago>
    """
    THUMBUP = 'T'
    THUMBDOWN = 'D'
    COMMENTED = 'C'
    REPLY = 'R'
    NOTIFICATION_TYPES = (
        (THUMBUP, _("dukung naik")),
        (THUMBDOWN, _("dukung turun")),
        (COMMENTED, _("berkomentar")),
        (REPLY, _("membalas"))
    )
    unread = models.BooleanField(default=True, db_index=True)
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    verb = models.CharField(max_length=1, choices=NOTIFICATION_TYPES)

    content_type = models.ForeignKey(
        ContentType, on_delete=models.CASCADE,
        related_name='notice_entity_notification',
        limit_choices_to=Q(app_label__in=['escort', 'person']))
    content_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'content_id')

    content_notified_id = models.PositiveIntegerField(null=True)
    content_notified_type = models.ForeignKey(
        ContentType, on_delete=models.CASCADE,
        related_name='notice_entity_notification_notified', null=True,
        limit_choices_to=Q(app_label__in=['escort', 'person']))
    content_notified_object = GenericForeignKey(
        'content_notified_type', 'content_notified_id')

    content_source_id = models.PositiveIntegerField(null=True)
    content_source_type = models.ForeignKey(
        ContentType, on_delete=models.CASCADE,
        related_name='notice_entity_notification_source', null=True,
        limit_choices_to=Q(app_label__in=['escort', 'person']))
    content_source_object = GenericForeignKey(
        'content_source_type', 'content_source_id')

    content_parent_id = models.PositiveIntegerField(null=True, blank=True)
    content_parent_type = models.ForeignKey(
        ContentType, on_delete=models.CASCADE,
        related_name='notice_entity_notification_parent',
        null=True, blank=True,
        limit_choices_to=Q(app_label__in=['escort', 'person']))
    content_parent_object = GenericForeignKey(
        'content_parent_type', 'content_parent_id')

    class Meta:
        abstract = True
        app_label = 'notice'
        ordering = ['-date_created']
        verbose_name = _("Notification")
        verbose_name_plural = _("Notifications")

    def __str__(self):
        if hasattr(self, 'actor'):
            content = self.content[:25] + '...' if self.content else None
            return f'{self.actor} {self.get_verb_display()} {content} {self.time_since()} ago'
        return self.get_verb_display()

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

    def time_since(self, now=None):
        """
        Shortcut for the ``django.utils.timesince.timesince`` function of the
        current timestamp.
        """
        from django.utils.timesince import timesince
        return timesince(self.date_created, now)

    def get_icon(self):
        """Model method to validate notification type and return the closest
        icon to the verb.
        """
        if self.verb == 'C':
            return 'fa-comment'

        elif self.verb == 'U':
            return 'fa-thumb-up'

        elif self.verb == 'D':
            return 'fa-thumb-down'

        elif self.verb == 'R':
            return 'fa-reply'

    def mark_as_read(self):
        if self.unread:
            self.unread = False
            self.save()

    def mark_as_unread(self):
        if not self.unread:
            self.unread = True
            self.save()


class AbstractNotificationActor(models.Model):
    actor = models.ForeignKey(
        'person.Person',
        related_name='notify_actor',
        on_delete=models.CASCADE)
    notification = models.ForeignKey(
        'notice.Notification',
        related_name='notify_actor_object',
        on_delete=models.CASCADE,
        null=True)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
        app_label = 'notice'
        ordering = ['-date_created']
        verbose_name = _("Notification Actor")
        verbose_name_plural = _("Notification Actors")


class AbstractNotificationRecipient(models.Model):
    recipient = models.ForeignKey(
        'person.Person',
        related_name='notify_recipient',
        on_delete=models.CASCADE)
    notification = models.ForeignKey(
        'notice.Notification',
        related_name='notify_recipient_object',
        on_delete=models.CASCADE,
        null=True)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
        app_label = 'notice'
        ordering = ['-date_created']
        verbose_name = _("Notification Recipient")
        verbose_name_plural = _("Notification Recipients")
