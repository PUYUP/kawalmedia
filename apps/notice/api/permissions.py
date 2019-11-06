import uuid

from rest_framework import permissions
from rest_framework.response import Response

from django.core.exceptions import ValidationError, ObjectDoesNotExist

# LOCAL UTILS
from utils.validators import get_model

Notification = get_model('notice', 'Notification')


class IsRecipientOrReject(permissions.BasePermission):
    """Notification Permission"""
    def has_permission(self, request, view):
        # Staff can always access CRUD
        if request.user.is_staff:
            return True

        # Only as person allowed
        if hasattr(request.user, 'person'):
            person_uuid = request.user.person.uuid
            current_uuid = view.kwargs['uuid']

            try:
                current_uuid = uuid.UUID(current_uuid)
            except ValueError:
                return False

            # Get object
            try:
                obj = Notification.objects.get(
                    uuid=current_uuid,
                    notify_recipient_object__recipient__uuid=person_uuid)
            except ObjectDoesNotExist:
                return False
            return True
        return False
