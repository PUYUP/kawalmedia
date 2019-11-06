import asyncio

from django.dispatch import receiver
from django.db.models import F
from django.contrib.contenttypes.models import ContentType

# PROJECT UTILS
from utils.validators import get_model

# NOTIFICATION UTILS
from ..notice.utils.asyncreate import create_notification

# LOCAL UTILS
from .utils.constant import PUBLISHED
from .utils.attributes import (
    set_attributes,
    update_attribute_values)

EntityLog = get_model('escort', 'EntityLog')
Notification = get_model('notice', 'Notification')

loop = asyncio.get_event_loop()


# Create signals
def media_handler(sender, instance, created, **kwargs):
    """Signals for Media action"""
    # Create attribute
    set_attributes(instance)

    # Execute only has request
    if hasattr(instance, 'request'):
        status = instance.status
        request = instance.request
        person = getattr(request.user, 'person', None)

        # Create process...
        log = EntityLog(content_object=instance, status=status, logger=person)
        log.save()

        # Update attributes
        data = request.data if hasattr(request, 'data') else None
        keys, values = list(), dict()

        if data is not None:
            for key in data:
                keys.append(key)
                values[key] = data[key]
            update_attribute_values(
                instance, identifiers=keys, values=values)


def rating_handler(sender, instance, created, **kwargs):
    """Signals for Rating action"""
    media = instance.media

    # Only new rating created
    if created:
        media.rating_count = F('rating_count') + 1
        media.save()


def rating_delete_handler(sender, instance, **kwargs):
    """Signals for Rating Delete action"""
    media = instance.media

    # Re-sum rating count
    if media.rating_count:
        media.rating_count = F('rating_count') - 1
        media.save()


def protest_init_handler(sender, instance, **kwargs):
    instance.__old_status = instance.status


def protest_handler(sender, instance, created, **kwargs):
    """Signals for Protest action"""
    media = instance.media
    status = instance.status
    old_status = instance.__old_status

    # Make sure this not from commented action
    # If status change to PUBLISHED, +1 count but old status is not PUBLISHED
    # If status change from PUBLISHED, -1 count but new status is not PUBLISHED
    if not hasattr(instance, 'comment_handler') and old_status != status:
        if status is PUBLISHED:
            media.protest_count = F('protest_count') + 1
            media.save()
        elif old_status is PUBLISHED:
            # But if not publish
            # Reduce protest count, but make sure count is ready
            if not created and media.protest_count:
                media.protest_count = F('protest_count') - 1
                media.save()

    # Execute only has request
    if hasattr(instance, 'request'):
        status = instance.status
        request = instance.request
        person = getattr(request.user, 'person', None)

        # Create process...
        log = EntityLog(content_object=instance, status=status, logger=person)
        log.save()


def protest_delete_handler(sender, instance, **kwargs):
    """Signal for Protest Delete action"""
    media = instance.media

    # Re-sum protest count
    if media.protest_count:
        media.protest_count = F('protest_count') - 1
        media.save()


def attribute_handler(sender, instance, created, **kwargs):
    if not created:
        """Assign this Attribute to all object
        Based on their content type entity"""
        pass


def thumbed_handler(sender, instance, created, **kwargs):
    """Signals for Thumbs action"""
    entity_object = getattr(instance, 'content_object', None)
    thumbing = instance.thumbing

    if (entity_object and hasattr(entity_object, 'thumbsup_count')
            and hasattr(entity_object, 'thumbsdown_count')):
        # Only new thumb created
        if created:
            if thumbing is True:
                entity_object.thumbsup_count = F('thumbsup_count') + 1

            if thumbing is False:
                entity_object.thumbsdown_count = F('thumbsdown_count') + 1

        if not created:
            """
            If thumb is UP reduce thumb DOWN and add thumb UP
            If thumb is DOWN reduce thumb UP and add thumb DOWN
            If thumb is null, no action
            """
            if thumbing is True and entity_object.thumbsdown_count:
                entity_object.thumbsdown_count = F('thumbsdown_count') - 1
                entity_object.thumbsup_count = F('thumbsup_count') + 1

            if thumbing is False and entity_object.thumbsup_count:
                entity_object.thumbsup_count = F('thumbsup_count') - 1
                entity_object.thumbsdown_count = F('thumbsdown_count') + 1

        entity_object.save()


def thumbed_delete_handler(sender, instance, **kwargs):
    """Signals for Thumbs Delete action"""
    entity_object = getattr(instance, 'content_object', None)
    thumbing = instance.thumbing

    if (entity_object and hasattr(entity_object, 'thumbsup_count')
            and hasattr(entity_object, 'thumbsdown_count')):
        # Re-sum count
        if thumbing is True:
            if entity_object.thumbsup_count:
                entity_object.thumbsup_count = F('thumbsup_count') - 1

        if thumbing is False:
            if entity_object.thumbsdown_count:
                entity_object.thumbsdown_count = F('thumbsdown_count') - 1

        entity_object.save()


def comment_handler(sender, instance, created, **kwargs):
    """Signals for Comment action"""
    protest = instance.protest
    media = getattr(protest, 'media', None)
    parent = getattr(instance, 'parent', None)

    # Only new protest created
    if created:
        # This indicate action from comment action
        setattr(protest, 'comment_handler', True)

        protest.comment_count = F('comment_count') + 1
        protest.save()

        if media:
            media.comment_count = F('comment_count') + 1
            media.save()

        if parent:
            parent.reply_count = F('reply_count') + 1
            parent.save()

        # Create notification
        loop.run_in_executor(None, create_notification, instance)


def comment_delete_handler(sender, instance, **kwargs):
    """Signals for Comment Delete action"""
    protest = instance.protest
    media = getattr(protest, 'media', None)
    parent = getattr(instance, 'parent', None)

    content_type = ContentType.objects.get_for_model(instance)
    notification = Notification.objects.filter(
        content_type=content_type.pk,
        content_id=instance.pk)

    if notification.exists():
        notification.delete()

    # Re-sum comment count
    if protest.comment_count:
        protest.comment_count = F('comment_count') - 1
        protest.save()

        if media and media.comment_count:
            media.comment_count = F('comment_count') - 1
            media.save()

    if parent and parent.reply_count:
        parent.reply_count = F('reply_count') - 1
        parent.save()
