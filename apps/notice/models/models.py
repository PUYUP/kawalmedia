from django.db import models

from .models_abstract import *
from utils.validators import is_model_registered

__all__ = list()


# 0
if not is_model_registered('notice', 'Notification'):
    class Notification(AbstractNotification):
        class Meta(AbstractNotification.Meta):
            db_table = 'notice_notification'

    __all__.append('Notification')


# 1
if not is_model_registered('notice', 'NotificationActor'):
    class NotificationActor(AbstractNotificationActor):
        class Meta(AbstractNotificationActor.Meta):
            db_table = 'notice_notification_actor'

    __all__.append('NotificationActor')


# 2
if not is_model_registered('notice', 'NotificationRecipient'):
    class NotificationRecipient(AbstractNotificationRecipient):
        class Meta(AbstractNotificationRecipient.Meta):
            db_table = 'notice_notification_recipient'

    __all__.append('NotificationRecipient')
