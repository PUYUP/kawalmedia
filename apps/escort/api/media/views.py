import itertools
from uuid import UUID

from django.conf import settings
from django.http import Http404
from django.db.models import (
    F, Q, Avg, Case, Value, When,
    BooleanField, FloatField)
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
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, NotAcceptable

# SERIALIZERS
from .serializers import (
    MediaSerializer,
    SingleMediaSerializer,
    CreateMediaSerializer
)

# ATTRIBUTES SERIALIZERS
from ..attribute.serializers import AttributeSerializer

# RATINGS SERIALIZERS
from ..rating.serializers import RatingSerializer, CreateRatingSerializer

# PERMISSIONS
from ..permissions import IsOwnerOrReject, IsCreatorOrReject

# PROJECT UTILS
from utils.validators import get_model

# LOCAL UTILS
from ...utils.constant import STATUS_CHOICES, PUBLISHED

Media = get_model('escort', 'Media')

# Define to avoid used ...().paginate__
PAGINATOR = PageNumberPagination()


@method_decorator(ensure_csrf_cookie, name='dispatch')
class MediaApiView(viewsets.ViewSet):
    lookup_field = 'uuid'
    permission_classes = (AllowAny,)
    permission_action = {
        # Disable update if not owner
        'partial_update': [IsCreatorOrReject]
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
        creator_uuid    = this person uuid
        person_uuid     = this current person logged in uuid
        status          = this status accepted from STATUS_CHOICES

        Logic like here
        ----------------------
        - If both NOT define; get objects with PUBLISHED status from all creator
        - If only creator_uuid define; get objects with PUBLISHED status from creator
        - If only status define; get objects with define status from current loggedin creator
        - If both define; get objects with PUBLISHED status only from creator

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
        q = Q()

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
        creator_uuid = kwargs.get('creator_uuid', None)
        if creator_uuid:
            try:
                creator_uuid = UUID(creator_uuid)
            except ValueError:
                raise NotFound(detail=_("UUID kreator tidak valid."))

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
        # So replace creator_uuid with person_uuid
        # But only if creator not define
        if status and creator_uuid is None:
            creator_uuid = person_uuid

        # Search creator exact by creator_uuid
        q_creator = Q(creator__uuid__exact=creator_uuid)

        # Only view published if not author
        if creator_uuid and status:
            if status != PUBLISHED and person_uuid != creator_uuid:
                raise NotAcceptable(detail=_("Konten ini dilindungi."))

        # General query for all
        # This if url don't has params creator and status
        # Show only published objects
        q = q_creator & ~Q(status=None) | Q(status=PUBLISHED)

        # Query objects by status and creator
        # If status define, show object from current user
        # Or if creator define, show object from current user
        if (status or creator_uuid) and person_uuid:
            q = q_creator & Q(status__exact=status)

        # If creator_uuid define get objects from the creator
        # But only published objects
        if (creator_uuid and status is None) \
                or (creator_uuid and status and person_uuid is None):
            q = q_creator & Q(status__exact=PUBLISHED)

        try:
            if uuid:
                try:
                    uuid = UUID(uuid)

                    # If not creator can only view published object status
                    # If current person is creator can see object (w/o status)
                    return Media.objects \
                        .prefetch_related('creator') \
                        .select_related('creator') \
                        .filter(
                            Q(uuid=uuid),
                            Q(creator=person) & ~Q(status=None) |
                            Q(status=PUBLISHED)) \
                        .annotate(
                            ownership=Case(
                                When(creator=person, then=Value(True)),
                                default=Value(False),
                                output_field=BooleanField()
                            )
                        ) \
                        .get()
                except ValueError:
                    raise Http404
            objs = Media.objects \
                .prefetch_related('creator') \
                .select_related('creator') \
                .annotate(
                    rating_average=Avg(
                        F('rating__score'), output_field=FloatField())
                ).filter(q, q_term)

            if limit:
                objs = objs[:int(limit)]

            return objs
        except ObjectDoesNotExist:
            raise Http404

    # Return a response
    def get_response(self, serializer, serializer_parent=None, *args, **kwargs):
        """ Output to endpoint """
        response = {}
        limit = kwargs.get('limit', None)

        if serializer.data and limit:
            response['count'] = int(limit)

        if not limit:
            if serializer_parent is not None:
                response['media'] = serializer_parent.data

            response['count'] = PAGINATOR.page.paginator.count
            response['navigate'] = {
                'previous': PAGINATOR.get_previous_link(),
                'next': PAGINATOR.get_next_link()
            }
        response['results'] = serializer.data
        return Response(response, status=response_status.HTTP_200_OK)

    # All items
    def list(self, request, format=None):
        """ View as item list """
        context = {'request': self.request}
        params = request.query_params

        creator_uuid = params.get('creator_uuid', None)
        status = params.get('status', None)
        term = params.get('term', None)
        match = params.get('match', None)
        limit = params.get('limit', None)

        queryset = self.get_object(creator_uuid=creator_uuid, limit=limit,
                                   status=status, term=term, match=match)

        if not limit:
            queryset = PAGINATOR.paginate_queryset(queryset, request)

        serializer = MediaSerializer(queryset, many=True, context=context)
        return self.get_response(serializer, limit=limit)

    # Single item
    def retrieve(self, request, uuid=None, format=None):
        """ View as single object """
        context = {'request': self.request}
        queryset = self.get_object(uuid)
        serializer = SingleMediaSerializer(
            queryset, many=False, context=context)
        return Response(serializer.data, status=response_status.HTTP_200_OK)

    # Create object
    @method_decorator(csrf_protect)
    @method_decorator(never_cache)
    @transaction.atomic
    def create(self, request, format=None):
        """ Create single object """
        context = {'request': self.request}
        serializer = CreateMediaSerializer(data=request.data, context=context)
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
        serializer = CreateMediaSerializer(
            instance=queryset,
            data=request.data,
            context=context,
            partial=True)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response(serializer.data, status=response_status.HTTP_200_OK)
        return Response(serializer.errors, status=response_status.HTTP_400_BAD_REQUEST)
