from uuid import UUID

from django.http import Http404
from django.db.models import F, Q
from django.db import transaction
from django.utils.translation import ugettext_lazy as _
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie
from django.views.decorators.cache import never_cache
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist

# THIRD PARTY
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status as response_status, viewsets
from rest_framework.pagination import PageNumberPagination
from rest_framework.exceptions import NotFound, NotAcceptable

# SERIALIZERS
from .serializers import ThumbedSerializer, CreateThumbedSerializer

# PERMISSIONS
from ..permissions import IsThumberOrReject

# PROJECT UTILS
from utils.validators import get_model

# LOCAL MODELS
from ...models.models import __all__ as model_index

Thumbed = get_model('escort', 'Thumbed')

# Define to avoid used ...().paginate__
PAGINATOR = PageNumberPagination()


class ThumbedApiView(viewsets.ViewSet):
    lookup_field = 'uuid'
    permission_classes = (AllowAny,)
    permission_action = {
        # Disable update if not owner
        'update': [IsThumberOrReject],
        'partial_update': [IsThumberOrReject]
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
        if uuid:
            try:
                uuid = UUID(uuid)
            except ValueError:
                raise NotFound()
        else:
            raise NotFound()

        queryset = Thumbed.objects \
            .prefetch_related('thumber', 'content_type') \
            .select_related('thumber', 'content_type') \
            .get(uuid=uuid)
        return queryset

    def list(self, request, format=None):
        context = {'request': self.request}
        return Response(status=response_status.HTTP_200_OK)

    # Single item
    def retrieve(self, request, uuid=None, format=None):
        """ View as single object """
        context = {'request': self.request}
        queryset = self.get_object(uuid=uuid)
        serializer = ThumbedSerializer(
            queryset, many=False, context=context)
        return Response(serializer.data, status=response_status.HTTP_200_OK)

    # Create object
    @method_decorator(csrf_protect)
    @method_decorator(never_cache)
    @transaction.atomic
    def create(self, request, format=None):
        """ Create single object """
        context = {'request': self.request}
        serializer = CreateThumbedSerializer(data=request.data, context=context)
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
        queryset = self.get_object(uuid=uuid)
        serializer = CreateThumbedSerializer(
            instance=queryset,
            data=request.data,
            context=context,
            partial=True)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response(serializer.data, status=response_status.HTTP_200_OK)
        return Response(serializer.errors, status=response_status.HTTP_400_BAD_REQUEST)
