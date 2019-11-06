# PROJECT UTILS
from utils.validators import get_model

NotificationActor = get_model('notice', 'NotificationActor')
NotificationRecipient = get_model('notice', 'NotificationRecipient')


def notification_handler(sender, instance, created, **kwargs):
    content_object = getattr(instance, 'content_object', None)
    content_type = getattr(instance, 'content_type', None)
    request = getattr(instance, 'request', None)
    user = getattr(request, 'user', None)
    model_name = content_type.model
    recipient = None

    if created:
        # Create actor
        if request and user:
            person = getattr(user, 'person', None)

            if person:
                NotificationActor.objects.create(
                    notification=instance, actor=person)

        # Create comment notify
        if model_name == 'comment':
            parent = getattr(content_object, 'parent', None)
            reply_for_person = getattr(content_object, 'reply_for_person', None)

            # Has parent replied to comment
            if parent:
                if not reply_for_person:
                    recipient = getattr(parent, 'commenter', None)
                else:
                    recipient = reply_for_person
            else:
                # Commented to protest
                protest = getattr(content_object, 'protest', None)
                recipient = getattr(protest, 'protester', None)

            if recipient:
                NotificationRecipient.objects.create(
                    notification=instance, recipient=recipient)
