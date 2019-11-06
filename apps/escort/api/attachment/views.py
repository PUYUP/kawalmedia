from uuid import UUID

from django.http import Http404
from django.db.models import F, Q
from django.db import transaction
from django.utils.translation import ugettext_lazy as _
from django.utils.text import slugify
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie
from django.views.decorators.cache import never_cache
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist

# THIRD PARTY
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.parsers import (
    FormParser, FileUploadParser, MultiPartParser)
from rest_framework import status as response_status, viewsets
from rest_framework.pagination import PageNumberPagination
from rest_framework.exceptions import NotFound, NotAcceptable

# SERIALIZERS
from .serializers import AttachmentSerializer, CreateAttachmentSerializer

# PERMISSIONS
from ..permissions import IsUploaderOrReject

# PROJECT UTILS
from utils.validators import get_model

# LOCAL MODELS
from ...models.models import __all__ as model_index

Attachment = get_model('escort', 'Attachment')

# Define to avoid used ...().paginate__
PAGINATOR = PageNumberPagination()


@method_decorator(ensure_csrf_cookie, name='dispatch')
class AttachmentApiView(viewsets.ViewSet):
    lookup_field = 'uuid'
    permission_classes = (AllowAny,)
    parser_class = (FormParser, FileUploadParser, MultiPartParser,)
    permission_action = {
        # Disable update if not owner
        'update': [IsUploaderOrReject],
        'partial_update': [IsUploaderOrReject]
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

    # Return a response
    def get_response(self, serializer, serializer_parent=None, *args, **kwargs):
        """ Output to endpoint """
        response = dict()
        limit = kwargs.get('limit', None)
        entity_type = kwargs.get('entity_type', None)

        if serializer.data and limit:
            response['count'] = int(limit)

        if not limit:
            if serializer_parent is not None:
                response[entity_type] = serializer_parent.data

            response['count'] = PAGINATOR.page.paginator.count
            response['navigate'] = {
                'previous': PAGINATOR.get_previous_link(),
                'next': PAGINATOR.get_next_link()
            }
        response['results'] = serializer.data
        return Response(response, status=response_status.HTTP_200_OK)

    # All Items
    def list(self, request, format=None):
        """
        entity_uuid = protest_uuid
        entity_index = model index for protest (for now is 7),
        """
        context = {'request': self.request}
        params = request.query_params
        entity_uuid = params.get('entity_uuid', None)
        entity_index = request.GET.get('entity_index', None)

        if not entity_index or not entity_uuid:
            raise NotFound()

        # Make sure entity_index as integer only
        try:
            entity_index = int(entity_index)
        except ValueError:
            raise NotFound()

        # Get the model entity by index
        try:
            entity_class = model_index[entity_index]
        except IndexError:
            raise NotFound()

        # Now get model object
        try:
            entity_model = get_model('escort', entity_class)
        except LookupError:
            raise NotFound()

        # ContentType berdasarkan entity (model)
        if entity_index or entity_index == 0:
            entity_type = ContentType.objects.get_for_model(entity_model)
        else:
            raise NotFound()

        # Check the uuid is valid
        try:
            entity_uuid = UUID(entity_uuid)
        except ValueError:
            raise NotFound()

        try:
            entity_object = entity_model.objects \
                .get(uuid=entity_uuid)
        except ObjectDoesNotExist:
            entity_object = None

        queryset = Attachment.objects \
            .prefetch_related('uploader', 'content_type') \
            .select_related('uploader', 'content_type') \
            .filter(content_type=entity_type)

        if entity_object:
            queryset = queryset.filter(object_id=entity_object.pk)

        queryset_paginator = PAGINATOR.paginate_queryset(queryset, request)
        serializer = AttachmentSerializer(
            queryset_paginator, many=True, context=context)
        return self.get_response(serializer, entity_type=slugify(entity_type))

    # Create object
    @method_decorator(csrf_protect)
    @method_decorator(never_cache)
    @transaction.atomic
    def create(self, request, format=None):
        """ Create single object """
        context = {'request': self.request}
        serializer = CreateAttachmentSerializer(data=request.data, context=context)
        if serializer.is_valid(raise_exception=True):
            attachment = serializer.save()
            return Response(serializer.data, status=response_status.HTTP_201_CREATED)
        return Response(serializer.errors, status=response_status.HTTP_400_BAD_REQUEST)
