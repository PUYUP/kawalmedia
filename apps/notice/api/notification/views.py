from uuid import UUID

from django.db.models import (
    Q, F, OuterRef, Subquery, Case, When, CharField, UUIDField)
from django.db import transaction
from django.utils.translation import ugettext_lazy as _
from django.utils.decorators import method_decorator
from django.core.exceptions import ObjectDoesNotExist
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie
from django.views.decorators.cache import never_cache

# THIRD PARTY
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status as response_status, viewsets
from rest_framework.pagination import PageNumberPagination
from rest_framework.exceptions import NotFound
from rest_framework.decorators import action

# SERIALIZERS
from .serializers import NotificationSerializer, CreateNotificationSerializer

# PROJECT UTILS
from utils.validators import get_model

# LOCAL PERMISSIONS
from ..permissions import IsRecipientOrReject

Notification = get_model('notice', 'Notification')
Comment = get_model('escort', 'Comment')
Protest = get_model('escort', 'Protest')
Media = get_model('escort', 'Media')

# Define to avoid used ...().paginate__
PAGINATOR = PageNumberPagination()


@method_decorator(ensure_csrf_cookie, name='dispatch')
class NotificationApiView(viewsets.ViewSet):
    """Listen all items action here..."""
    lookup_field = 'uuid'
    permission_classes = (IsAuthenticated,)
    permission_action = {
        # Disable update if not owner
        'partial_update': [IsRecipientOrReject],
        'destroy': [IsRecipientOrReject]
    }

    def get_permissions(self):
        """
        Instantiates and returns
        the list of permissions that this view requires.
        """
        try:
            # return permission_classes depending on `action`
            return [permission() for permission in self.permission_action
                    [self.action]]
        except KeyError:
            # action is not set return default permission_classes
            return [permission() for permission in self.permission_classes]

    # Get a objects
    def get_object(self, uuid=None, *agrs, **kwargs):
        if type(uuid) is not UUID:
            try:
                uuid = UUID(uuid)
            except ValueError:
                uuid = None

        if not uuid:
            raise NotFound()

        try:
            queryset = Notification.objects.get(uuid=uuid)
        except ObjectDoesNotExist:
            raise NotFound()

        return queryset

    # Return a response
    def get_response(self, serializer, serializer_parent=None, *args, **kwargs):
        """ Output to endpoint """
        response = dict()
        response['count'] = PAGINATOR.page.paginator.count
        response['navigate'] = {
            'previous': PAGINATOR.get_previous_link(),
            'next': PAGINATOR.get_next_link()
        }

        response['results'] = serializer.data
        return Response(response, status=response_status.HTTP_200_OK)

    def list(self, request, format=None):
        context = {'request': self.request}
        params = request.query_params

        # The person
        person = getattr(self.request.user, 'person', None)

        comment = Comment.objects.filter(pk=OuterRef('content_id'))
        protest = Protest.objects.filter(pk=OuterRef('content_id'))

        comment_notified = Comment.objects.filter(pk=OuterRef('content_notified_id'))
        protest_notified = Protest.objects.filter(pk=OuterRef('content_notified_id'))

        media_source = Media.objects.filter(pk=OuterRef('content_source_id'))

        media_parent = Media.objects.filter(pk=OuterRef('content_parent_id'))
        protest_parent = Protest.objects.filter(pk=OuterRef('content_parent_id'))

        # Get protest objects...
        queryset = Notification.objects \
            .prefetch_related('content_type', 'content_notified_type', 'content_source_type') \
            .select_related('content_type', 'content_notified_type', 'content_source_type') \
            .annotate(
                actor=F('notify_actor_object__actor__user__username'),
                recipient=F('notify_recipient_object__recipient__user__username'),
                content=Case(
                    When(
                        Q(content_type__model='comment'),
                        then=Subquery(comment.values('description')[:1])
                    ),
                    When(
                        Q(content_type__model='protest'),
                        then=Subquery(protest.values('label')[:1])
                    ),
                    default=None,
                    output_field=CharField()
                ),
                content_uuid=Case(
                    When(
                        Q(content_type__model='comment'),
                        then=Subquery(comment.values('uuid')[:1])
                    ),
                    When(
                        Q(content_type__model='protest'),
                        then=Subquery(protest.values('uuid')[:1])
                    ),
                    default=None,
                    output_field=UUIDField()
                ),
                content_notified=Case(
                    When(
                        Q(content_notified_type__model='comment'),
                        then=Subquery(comment_notified.values('description')[:1])
                    ),
                    When(
                        Q(content_notified_type__model='protest'),
                        then=Subquery(protest_notified.values('label')[:1])
                    ),
                    default=None,
                    output_field=CharField()
                ),
                content_notified_uuid=Case(
                    When(
                        Q(content_notified_type__model='comment'),
                        then=Subquery(comment_notified.values('uuid')[:1])
                    ),
                    When(
                        Q(content_notified_type__model='protest'),
                        then=Subquery(protest_notified.values('uuid')[:1])
                    ),
                    default=None,
                    output_field=UUIDField()
                ),
                content_source_uuid=Case(
                    When(
                        Q(content_source_type__model='media'),
                        then=Subquery(media_source.values('uuid')[:1])
                    ),
                    default=None,
                    output_field=UUIDField()
                ),
                content_parent_uuid=Case(
                    When(
                        Q(content_parent_type__model='media'),
                        then=Subquery(media_parent.values('uuid')[:1])
                    ),
                    When(
                        Q(content_parent_type__model='protest'),
                        then=Subquery(protest_parent.values('uuid')[:1])
                    ),
                    default=None,
                    output_field=UUIDField()
                ),
            ) \
            .filter(notify_recipient_object__recipient=person)

        queryset_paginator = PAGINATOR.paginate_queryset(
            queryset, request)
        serializer = NotificationSerializer(
            queryset_paginator, many=True, context=context)
        return self.get_response(serializer)

    # Update item data
    @method_decorator(csrf_protect)
    @method_decorator(never_cache)
    @transaction.atomic
    def partial_update(self, request, uuid=None, format=None):
        """Update a item... """
        context = {'request': self.request}
        queryset = self.get_object(uuid=uuid)
        serializer = CreateNotificationSerializer(
            instance=queryset,
            data=request.data,
            context=context,
            partial=True)
        if serializer.is_valid(raise_exception=True):
            notification = serializer.save()
            return Response(serializer.data, status=response_status.HTTP_200_OK)
        return Response(serializer.errors, status=response_status.HTTP_400_BAD_REQUEST)

    # Delete...
    @method_decorator(csrf_protect)
    @method_decorator(never_cache)
    @transaction.atomic
    def destroy(self, request, uuid=None):
        queryset = self.get_object(uuid)
        queryset.delete()
        return Response(
            {'detail': _("Berhasil dihapus.")},
            status=response_status.HTTP_204_NO_CONTENT)

    @method_decorator(csrf_protect)
    @method_decorator(never_cache)
    @transaction.atomic
    @action(methods=['post'], detail=False, permission_classes=[IsAuthenticated],
            url_path='mark-reads', url_name='mark_reads')
    def mark_reads(self, request):
        # The person
        person = getattr(self.request.user, 'person', None)

        try:
            queryset = Notification.objects \
                .filter(
                    notify_recipient_object__recipient=person,
                    unread=True)
        except ObjectDoesNotExist:
            raise NotFound()

        queryset.update(unread=False)
        return Response(status=response_status.HTTP_200_OK)

    @method_decorator(csrf_protect)
    @method_decorator(never_cache)
    @transaction.atomic
    @action(methods=['delete'], detail=False, permission_classes=[IsAuthenticated],
            url_path='delete-all', url_name='delete_all')
    def delete_all(self, request):
        # The person
        person = getattr(self.request.user, 'person', None)

        try:
            queryset = Notification.objects \
                .filter(notify_recipient_object__recipient=person)
        except ObjectDoesNotExist:
            raise NotFound()

        queryset.delete()
        return Response(status=response_status.HTTP_200_OK)

    @method_decorator(csrf_protect)
    @method_decorator(never_cache)
    @transaction.atomic
    @action(methods=['get'], detail=False, permission_classes=[IsAuthenticated],
            url_path='get-count', url_name='get_count')
    def get_count(self, request):
        # The person
        person = getattr(self.request.user, 'person', None)

        try:
            queryset = Notification.objects \
                .filter(
                    notify_recipient_object__recipient=person,
                    unread=True)
        except ObjectDoesNotExist:
            raise NotFound()

        count = queryset.count()
        return Response({'count': int(count)}, status=response_status.HTTP_200_OK)
