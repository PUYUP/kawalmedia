import uuid

from rest_framework import permissions
from rest_framework.response import Response

from django.core.exceptions import ValidationError, ObjectDoesNotExist

# LOCAL UTILS
from ..utils.constant import PUBLISHED
from utils.validators import get_model

Attachment = get_model('escort', 'Attachment')


class IsUploaderOrReject(permissions.BasePermission):
    """Attachment Permission"""
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

            # Get attachment
            try:
                attachment = Attachment.objects.get(uuid=current_uuid)
            except ObjectDoesNotExist:
                return False
            return attachment.uploader.uuid == person_uuid
        return False
