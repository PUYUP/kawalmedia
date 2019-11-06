from django.apps import AppConfig
from django.db.models.signals import post_save, post_delete, post_init


class NoticeConfig(AppConfig):
    name = 'apps.notice'

    def ready(self):
        from apps.notice.signals import notification_handler
        from utils.validators import get_model

        # Create notification
        try:
            Notification = get_model('notice', 'Notification')
        except LookupError:
            Notification = None

        if Notification:
            post_save.connect(
                notification_handler, sender=Notification,
                dispatch_uid='notification_signal')
