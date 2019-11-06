from uuid import UUID

from rest_framework import permissions
from rest_framework.response import Response

from django.core.exceptions import ValidationError, ObjectDoesNotExist

# LOCAL UTILS
from ..utils.constant import PUBLISHED
from utils.validators import get_model

# LOCAL MODELS
from ..models.models import __all__ as model_index

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
                current_uuid = UUID(current_uuid)
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
                current_uuid = UUID(current_uuid)
            except ValueError:
                return False

            # Get media
            try:
                media = Media.objects.get(
                    uuid=current_uuid,
                    creator__uuid=person_uuid)
            except ObjectDoesNotExist:
                return False
            return True
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
                current_uuid = UUID(current_uuid)
            except ValueError:
                return False

            # Get protest
            try:
                protest = Protest.objects.get(
                    uuid=current_uuid,
                    protester__uuid=person_uuid)
            except ObjectDoesNotExist:
                return False
            return True
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
                current_uuid = UUID(current_uuid)
            except ValueError:
                return False

            # Get rating
            try:
                rating = Rating.objects.get(
                    uuid=current_uuid,
                    rater__uuid=person_uuid)
            except ObjectDoesNotExist:
                return False
            return True
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
                current_uuid = UUID(current_uuid)
            except ValueError:
                return False

            # Get thumb
            try:
                thumb = Thumbed.objects.get(
                    uuid=current_uuid,
                    thumber__uuid=person_uuid)
            except ObjectDoesNotExist:
                return False
            return True
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
                current_uuid = UUID(current_uuid)
            except ValueError:
                return False

            # Get attachment
            try:
                attachment = Attachment.objects.get(
                    uuid=current_uuid,
                    uploader__uuid=person_uuid)
            except ObjectDoesNotExist:
                return False
            return True
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
                current_uuid = UUID(current_uuid)
            except ValueError:
                return False

            # Get comment
            try:
                comment = Comment.objects.get(
                    uuid=current_uuid,
                    commenter__uuid=person_uuid)
            except ObjectDoesNotExist:
                return False
            return True
        return False


class IsEntityOwnerOrReject(permissions.BasePermission):
    """Entity Permission"""
    def has_permission(self, request, view):
        # Staff can always access CRUD
        if request.user.is_staff:
            return True

        # Only as person allowed
        person = getattr(request.user, 'person', None)
        if person:
            person_uuid = person.uuid
            entity_index = request.data.get('entity_index', None)
            entity_uuid = request.data.get('entity_uuid', None)

            if request.method == 'DELETE':
                entity_index = request.GET.get('entity_index', None)
                entity_uuid = request.GET.get('entity_uuid', None)

            if entity_index is None or not entity_uuid:
                return False

            # Make sure entity_index as integer only
            try:
                entity_index = int(entity_index)
            except ValueError:
                return False

            try:
                entity_uuid = UUID(entity_uuid)
            except ValueError:
                return False

            # Get the model entity by index
            try:
                entity_class = model_index[entity_index]
            except IndexError:
                return False

            # Now get model object
            try:
                entity_model = get_model('escort', entity_class)
            except LookupError:
                return False

            model_name = entity_model._meta.model_name  # ex: media, comment

            if model_name == 'media':
                try:
                    entity_object = entity_model.objects.get(
                        uuid=entity_uuid, creator__uuid=person_uuid)
                except ObjectDoesNotExist:
                    return False
                return True
            return False
        return False
