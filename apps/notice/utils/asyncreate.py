import asyncio

from django.contrib.contenttypes.models import ContentType

# PROJECT UTILS
from utils.validators import get_model

Notification = get_model('notice', 'Notification')
NotificationActor = get_model('notice', 'NotificationActor')
NotificationRecipient = get_model('notice', 'NotificationRecipient')


def create_notification(instance, *agrs, **kwargs):
    """How notification work?
    - Main entity           = content_notified_type & content_notified_id
        - Sub entity        = content_type & content_id
        - Sub entity        = content_notified_type & content_notified_id
            - Child entity  = content_type & content_id

    Notification model save the instance (current user created)
    And target notified also saved
    Create if current instance creator not same with notified instnace creator
    """
    content_type = ContentType.objects.get_for_model(instance)
    model_name = content_type.model

    # Start create notification for Comment
    if model_name == 'comment':
        parent = getattr(instance, 'parent', None)
        protest = getattr(instance, 'protest', None)
        request = getattr(instance, 'request', None)
        user = getattr(request, 'user', None)
        person = getattr(user, 'person', None)
        reply_for_person = getattr(instance, 'reply_for_person', None)
        content_source_type = ContentType.objects.get_for_model(instance.protest.media)

        # Has parent indicated replied to comment
        if parent and person:
            if parent.commenter == person and not reply_for_person:
                return None

            content_notified_type = ContentType.objects.get_for_model(parent)
            content_parent_type = ContentType.objects.get_for_model(instance.protest)

            notification = Notification(
                content_object=instance,
                content_type=content_type,
                content_notified_object=parent,
                content_notified_type=content_notified_type,
                content_source_object=instance.protest.media,
                content_source_type=content_source_type,
                content_parent_object=instance.protest,
                content_parent_type=content_parent_type)
            notification.verb = 'R'

        # No parent indicated commented to Protest
        if not parent and protest and person:
            if protest.protester == person:
                return None

            content_notified_type = ContentType.objects.get_for_model(protest)

            notification = Notification(
                content_object=instance,
                content_type=content_type,
                content_notified_object=protest,
                content_notified_type=content_notified_type,
                content_source_object=instance.protest.media,
                content_source_type=content_source_type)
            notification.verb = 'C'

        # This request send to signals
        if request:
            setattr(notification, 'request', request)

        notification.save()
