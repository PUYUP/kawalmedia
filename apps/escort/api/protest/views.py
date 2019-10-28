import itertools
from uuid import UUID

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
    ProtestSerializer, CreateProtestSerializer,
    SingleProtestSerializer)

# MEDIA SERIALIZERS
from ..media.serializers import SingleMediaSerializer

# PERMISSIONS
from ..permissions import IsProtesterOrReject, IsThumberOrReject

# PROJECT UTILS
from utils.validators import get_model

# LOCAL UTILS
from ...utils.constant import STATUS_CHOICES, PUBLISHED, DRAFT

Protest = get_model('escort', 'Protest')
Media = get_model('escort', 'Media')

# Define to avoid used ...().paginate__
PAGINATOR = PageNumberPagination()


@method_decorator(ensure_csrf_cookie, name='dispatch')
class ProtestApiView(viewsets.ViewSet):
    """Listen all protest action here..."""
    lookup_field = 'uuid'
    permission_classes = (AllowAny,)
    permission_action = {
        # Disable update if not owner
        'partial_update': [IsProtesterOrReject],
        'destroy': [IsProtesterOrReject]
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
        """
        Fetches objects
        Parameters is;
        ----------------------
        protester_uuid   = this person uuid
        person_uuid     = this current person logged in uuid
        status          = this status accepted from STATUS_CHOICES

        Logic like here
        ----------------------
        - If both NOT define; get objects with PUBLISHED status from all protester
        - If only protester_uuid define; get objects with PUBLISHED status from protester
        - If only status define; get objects with define status from current loggedin protester
        - If both define; get objects with PUBLISHED status only from protester

        Note
        ----------------------
        - If status define but user not logged, don't have effect
        """

        # Start here...
        person = None
        person_uuid = None
        term = kwargs.get('term', None)
        match = kwargs.get('match', None)
        limit = kwargs.get('limit', None)
        media_uuid = kwargs.get('media_uuid', None)
        q = Q()

        # Media define, show only from this media
        q_media = q
        if media_uuid:
            q_media = Q(media__uuid=media_uuid)

        # Search objects
        q_term = q
        if term:
            if match:
                q_term = Q(label__iexact=term)
            else:
                q_term = Q(label__icontains=term)

        # The person
        if self.request.user.is_authenticated:
            if hasattr(self.request.user, 'person'):
                person = self.request.user.person
                person_uuid = person.uuid

        # Creator uuid defined
        # But before use validated first
        protester_uuid = kwargs.get('protester_uuid', None)
        if protester_uuid:
            if type(protester_uuid) is not UUID:
                try:
                    protester_uuid = UUID(protester_uuid)
                except ValueError:
                    raise NotFound()

        # Status defined
        # Validate to make sure status defined
        status = kwargs.get('status', None)
        if status:
            if not status.isdigit():
                raise NotFound(detail=_("Status harus angka."))

            # Status must integer
            status = int(status)
            if (status not in itertools.chain(*STATUS_CHOICES)):
                raise NotFound(detail=_("Status tidak tersedia."))

        # If status defined get objects from current user
        # So replace protester_uuid with person_uuid
        # But only if protester not define
        if status and protester_uuid is None:
            protester_uuid = person_uuid

        # Search protester exact by protester_uuid
        q_protester = Q(protester__uuid__exact=protester_uuid)

        # Only view published if not author
        if protester_uuid and status:
            if status != PUBLISHED and person_uuid != protester_uuid:
                raise NotAcceptable(detail=_("Konten ini dilindungi."))

        # General query for all
        # This if url don't has params protester and status
        # Show only published objects
        q = q_protester & ~Q(status=None) | Q(status=PUBLISHED)

        # Query objects by status and protester
        # If status define, show object from current user
        # Or if protester define, show object from current user
        if (status or protester_uuid) and person_uuid:
            q = q_protester & Q(status__exact=status)

        # If protester_uuid define get objects from the protester
        # But only published objects
        if (protester_uuid and status is None) \
                or (protester_uuid and status and person_uuid is None):
            q = q_protester & Q(status__exact=PUBLISHED)

        try:
            if uuid:
                if type(uuid) is not UUID:
                    try:
                        uuid = UUID(uuid)
                    except ValueError:
                        raise NotFound()

                # If not protester can only view published object status
                # If current person is protester can see object (w/o status)
                queryset = Protest.objects \
                    .prefetch_related('protester', 'protester__user__person', 'media') \
                    .select_related('protester', 'protester__user__person', 'media') \
                    .filter(
                        Q(uuid=uuid),
                        Q(protester=person) & ~Q(status=None) |
                        Q(status=PUBLISHED)) \
                    .annotate(
                        ownership=Case(
                            When(protester=person, then=Value(True)),
                            default=Value(False),
                            output_field=BooleanField()
                        )
                    )

                # Make sub-query for avatar only
                person_avatar = queryset.filter(
                    protester__attribute_values__person=OuterRef('protester'),
                    protester__attribute_values__attribute__identifier='avatar')

                person_thumbing = queryset.filter(
                    thumbs__thumber=person,
                    thumbs__thumbing__isnull=False,
                    thumbs__object_id=F('pk'))

                # Append avatar
                queryset = queryset.annotate(
                    avatar=Subquery(
                        person_avatar
                        .values('protester__attribute_values__value_image')[:1]),

                    thumbing=Subquery(
                        person_thumbing
                        .values('thumbs__thumbing')[:1]),

                    thumbing_uuid=Subquery(
                        person_thumbing
                        .values('thumbs__uuid')[:1]))
                return queryset.get()

            # List objects
            queryset = Protest.objects \
                .prefetch_related('protester', 'protester__user__person', 'media') \
                .select_related('protester', 'protester__user__person', 'media') \
                .filter(q, q_term, q_media)

            # Make sub-query for avatar only
            person_avatar = queryset.filter(
                protester__attribute_values__person=OuterRef('protester'),
                protester__attribute_values__attribute__identifier='avatar')

            # Append avatar
            queryset = queryset.annotate(
                avatar=Subquery(
                    person_avatar
                    .values('protester__attribute_values__value_image')[:1]))

            if limit:
                queryset = queryset[:int(limit)]

            return queryset
        except ObjectDoesNotExist:
            raise NotFound(detail=_("Tidak ditemukan."))

    # Return a response
    def get_response(self, serializer, serializer_parent=None, *args, **kwargs):
        """ Output to endpoint """
        response = {}
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
        media_uuid = params.get('media_uuid', None)
        protester_uuid = params.get('protester_uuid', None)
        status = params.get('status', None)
        term = params.get('term', None)
        match = params.get('match', None)
        limit = params.get('limit', None)

        if media_uuid:
            if type(media_uuid) is not UUID:
                try:
                    media_uuid = UUID(media_uuid)
                except ValueError:
                    raise NotFound()

        # Get protest objects...
        queryset = self.get_object(
            protester_uuid=protester_uuid, media_uuid=media_uuid,
            limit=limit, status=status, term=term, match=match)

        queryset_paginator = PAGINATOR.paginate_queryset(
            queryset, request)
        serializer = ProtestSerializer(
            queryset_paginator, many=True, context=context)
        return self.get_response(serializer)

    # Single item
    def retrieve(self, request, uuid=None, format=None):
        """ View as single object """
        context = {'request': self.request}
        queryset = self.get_object(uuid)
        serializer = SingleProtestSerializer(
            queryset, many=False, context=context)
        return Response(serializer.data, status=response_status.HTTP_200_OK)

    # Create object
    @method_decorator(csrf_protect)
    @method_decorator(never_cache)
    @transaction.atomic
    def create(self, request, format=None):
        """ Create single object """
        context = {'request': self.request}
        serializer = CreateProtestSerializer(data=request.data, context=context)
        if serializer.is_valid(raise_exception=True):
            media = serializer.save()
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
        serializer = CreateProtestSerializer(
            instance=queryset,
            data=request.data,
            context=context,
            partial=True)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response(serializer.data, status=response_status.HTTP_200_OK)
        return Response(serializer.errors, status=response_status.HTTP_400_BAD_REQUEST)

    # Delete...
    @method_decorator(csrf_protect)
    @method_decorator(never_cache)
    @transaction.atomic
    def destroy(self, request, uuid=None):
        queryset = self.get_object(uuid)
        if queryset.status == DRAFT:
            queryset.delete()

            return Response(
                {'detail': _("Berhasil dihapus.")},
                status=response_status.HTTP_204_NO_CONTENT)

        return Response(
            {'detail': _("Konten terpublikasi tidak bisa dihapus.")},
            status=response_status.HTTP_401_UNAUTHORIZED)
