import uuid

from rest_framework import permissions
from rest_framework.response import Response

from django.core.exceptions import ValidationError


class IsOwnerOrReject(permissions.BasePermission):
    """
    Validate current user is self
    If not access read only
    """

    def has_permission(self, request, view):
        # Staff can always access CRUD
        if request.user.is_staff:
            return True

        # Only as person allowed
        if hasattr(request.user, 'person'):
            user_uuid = request.user.person.uuid
            current_uuid = view.kwargs['uuid']

            try:
                current_uuid = uuid.UUID(current_uuid)
            except ValueError:
                return False
            return current_uuid == user_uuid
        return False
