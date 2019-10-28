import uuid

from rest_framework import permissions
from rest_framework.response import Response

from django.core.exceptions import ValidationError, ObjectDoesNotExist

# LOCAL UTILS
from ..utils.constant import PUBLISHED
from utils.validators import get_model

Media = get_model('escort', 'Media')
Protest = get_model('escort', 'Protest')
Comment = get_model('escort', 'Comment')
Thumbed = get_model('escort', 'Thumbed')
Rating = get_model('escort', 'Rating')
Attachment = get_model('escort', 'Attachment')


class IsOwnerOrReject(permissions.BasePermission):
    """General Permission"""
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


class IsCreatorOrReject(permissions.BasePermission):
    """Media Permission"""
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

            # Get media
            try:
                media = Media.objects.get(uuid=current_uuid)
            except ObjectDoesNotExist:
                return False
            return media.creator.uuid == person_uuid
        return False


class IsProtesterOrReject(permissions.BasePermission):
    """Protest Permission"""
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

            # Get protest
            try:
                protest = Protest.objects.get(uuid=current_uuid)
            except ObjectDoesNotExist:
                return False
            return protest.protester.uuid == person_uuid
        return False


class IsRaterOrReject(permissions.BasePermission):
    """Rating Permission"""
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

            # Get rating
            try:
                rating = Rating.objects.get(uuid=current_uuid)
            except ObjectDoesNotExist:
                return False
            return rating.rater.uuid == person_uuid
        return False


class IsThumberOrReject(permissions.BasePermission):
    """Thumbed Permission"""
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

            # Get thumb
            try:
                thumb = Thumbed.objects.get(uuid=current_uuid)
            except ObjectDoesNotExist:
                return False
            return thumb.thumber.uuid == person_uuid
        return False


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


class IsCommenterOrReject(permissions.BasePermission):
    """Comment Permission"""
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

            # Get comment
            try:
                comment = Comment.objects.get(uuid=current_uuid)
            except ObjectDoesNotExist:
                return False
            return comment.commenter.uuid == person_uuid
        return False
