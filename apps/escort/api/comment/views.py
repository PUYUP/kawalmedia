from uuid import UUID
from itertools import chain

from django.db.models import (
    F, Q, Case, Value, When, BooleanField,
    OuterRef, Subquery)
from django.db import transaction
from django.utils.translation import ugettext_lazy as _
from django.utils.decorators import method_decorator
from django.core.exceptions import ObjectDoesNotExist
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie
from django.views.decorators.cache import never_cache

# THIRD PARTY
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status as response_status, viewsets
from rest_framework.pagination import PageNumberPagination
from rest_framework.exceptions import NotFound

# SERIALIZERS
from .serializers import (
    CommentSerializer, CreateCommentSerializer,
    SingleCommentSerializer)

# MEDIA SERIALIZERS
from ..protest.serializers import SingleProtestSerializer

# PERMISSIONS
from ..permissions import IsCommenterOrReject

# PROJECT UTILS
from utils.validators import get_model

# LOCAL UTILS
from ...utils.constant import STATUS_CHOICES, PUBLISHED, DRAFT

Protest = get_model('escort', 'Protest')
Comment = get_model('escort', 'Comment')

# Define to avoid used ...().paginate__
PAGINATOR = PageNumberPagination()


@method_decorator(ensure_csrf_cookie, name='dispatch')
class CommentApiView(viewsets.ViewSet):
    """Listen all protest action here..."""
    lookup_field = 'uuid'
    permission_classes = (AllowAny,)
    permission_action = {
        # Disable update if not owner
        'partial_update': [IsCommenterOrReject],
        'destroy': [IsCommenterOrReject]
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
        limit = kwargs.get('limit', None)
        protest_uuid = kwargs.get('protest_uuid', None)
        parent_uuid = kwargs.get('parent_uuid', None)
        notified_uuid = kwargs.get('notified_uuid', None)

        # The person
        person = getattr(self.request.user, 'person', None)

        try:
            if uuid:
                if type(uuid) is not UUID:
                    try:
                        uuid = UUID(uuid)
                    except ValueError:
                        raise NotFound()

                # If not commenter can only view published object status
                # If current person is commenter can see object (w/o status)
                queryset = Comment.objects \
                    .prefetch_related('commenter', 'commenter__user__person', 'protest') \
                    .select_related('commenter', 'commenter__user__person', 'protest') \
                    .filter(Q(uuid=uuid)) \
                    .annotate(
                        ownership=Case(
                            When(commenter=person, then=Value(True)),
                            default=Value(False),
                            output_field=BooleanField()
                        )
                    )

                # Make sub-query for avatar only
                person_avatar = queryset.filter(
                    commenter__attribute_values__person=OuterRef('commenter'),
                    commenter__attribute_values__attribute__identifier='avatar')

                # Append avatar
                queryset = queryset.annotate(
                    avatar=Subquery(
                        person_avatar
                        .values('commenter__attribute_values__value_image')[:1])
                )
                return queryset.get()

            # List objects
            queryset = Comment.objects \
                .prefetch_related(
                    'commenter', 'commenter__user__person', 'protest',
                    'reply_to_comment__parent', 'reply_for_person__user__person') \
                .select_related(
                    'commenter', 'commenter__user__person', 'protest',
                    'reply_to_comment__parent', 'reply_for_person__user__person') \
                .filter(protest__uuid=protest_uuid)

            # Get objects with parent
            if parent_uuid:
                if type(parent_uuid) is not UUID:
                    try:
                        parent_uuid = UUID(parent_uuid)
                    except ValueError:
                        parent_uuid = None

                if parent_uuid:
                    queryset = queryset.filter(parent__uuid=parent_uuid)
            else:
                queryset = queryset.filter(
                    Q(parent__isnull=True) | Q(parent=0),
                    Q(reply_to_comment__isnull=True),
                    Q(reply_for_person__isnull=True))

            # Make sub-query for avatar only
            person_avatar = queryset.filter(
                commenter__attribute_values__person=OuterRef('commenter'),
                commenter__attribute_values__attribute__identifier='avatar')

            # Append avatar
            queryset = queryset.annotate(
                ownership=Case(
                    When(commenter=person, then=Value(True)),
                    default=Value(False),
                    output_field=BooleanField()),

                avatar=Subquery(
                    person_avatar
                    .values('commenter__attribute_values__value_image')[:1]))

            if limit:
                queryset = queryset[:int(limit)]

            # If notification we get prev and next value from current content
            if notified_uuid:
                if type(parent_uuid) is not UUID:
                    try:
                        notified_uuid = UUID(notified_uuid)
                    except ValueError:
                        notified_uuid = None

                if notified_uuid:
                    x = queryset.filter(uuid=notified_uuid)

                    if x.exists():
                        y = queryset.filter(date_created__lt=x.get().date_created)[:5]
                        z = queryset.filter(date_created__gt=x.get().date_created)[:5]
                        queryset = sorted(
                            chain(x, y, z), 
                            key=lambda queryset: queryset.date_created, 
                            reverse=True)

            return queryset
        except ObjectDoesNotExist:
            raise NotFound(detail=_("Tidak ditemukan."))

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
        protest_uuid = params.get('protest_uuid', None)
        parent_uuid = params.get('parent_uuid', None)
        notified_uuid = params.get('notified_uuid', None)
        limit = params.get('limit', None)

        if protest_uuid:
            try:
                protest_uuid = UUID(protest_uuid)
            except ValueError:
                raise NotFound()

        # Get protest objects...
        queryset = self.get_object(
            protest_uuid=protest_uuid, limit=limit, parent_uuid=parent_uuid,
            notified_uuid=notified_uuid)
        queryset_paginator = PAGINATOR.paginate_queryset(
            queryset, request)
        serializer = CommentSerializer(
            queryset_paginator, many=True, context=context)
        return self.get_response(serializer)

    # Single item
    def retrieve(self, request, uuid=None, format=None):
        """ View as single object """
        context = {'request': self.request}
        queryset = self.get_object(uuid)
        serializer = SingleCommentSerializer(
            queryset, many=False, context=context)
        return Response(serializer.data, status=response_status.HTTP_200_OK)

    # Create object
    @method_decorator(csrf_protect)
    @method_decorator(never_cache)
    @transaction.atomic
    def create(self, request, format=None):
        """ Create single object """
        context = {'request': self.request}
        serializer = CreateCommentSerializer(data=request.data, context=context)
        if serializer.is_valid(raise_exception=True):
            comment = serializer.save()
            queryset = self.get_object(uuid=comment.uuid)
            serializer = SingleCommentSerializer(
                queryset, many=False, context=context)
            return Response(serializer.data, status=response_status.HTTP_201_CREATED)
        return Response(serializer.errors, status=response_status.HTTP_400_BAD_REQUEST)

    # Update item data
    @method_decorator(csrf_protect)
    @method_decorator(never_cache)
    @transaction.atomic
    def partial_update(self, request, uuid=None, format=None):
        """Update a item... """
        context = {'request': self.request}
        queryset = self.get_object(uuid)
        serializer = CreateCommentSerializer(
            instance=queryset,
            data=request.data,
            context=context,
            partial=True)
        if serializer.is_valid(raise_exception=True):
            comment = serializer.save()
            queryset = self.get_object(uuid=comment.uuid)
            serializer = SingleCommentSerializer(
                queryset, many=False, context=context)
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
