from uuid import UUID
from itertools import chain

from django.db.models import F, Q
from django.db import transaction
from django.utils.translation import ugettext_lazy as _
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.cache import never_cache
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import FieldError, ObjectDoesNotExist

# THIRD PARTY
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.parsers import (
    FormParser, FileUploadParser, MultiPartParser)
from rest_framework import status as response_status, viewsets
from rest_framework.exceptions import NotFound, NotAcceptable

# SERIALIZERS
from .serializers import (
    AttributeSerializer, AttributeValueSerializer,
    CreateAttributeValueSerializer)

# PERMISSIONS
from ..permissions import (
    IsEntityOwnerOrReject, IsCreatorOrReject,
    IsOwnerOrReject)

# PROJECT UTILS
from utils.validators import get_model

# LOCAL UTILS
from ...utils.attributes import update_attribute_values
from ...utils.constant import (
    CLASSIFICATION_CHOICES, PUBLICATION_CHOICES)

# LOCAL MODELS
from ...models.models import __all__ as model_index

Media = get_model('escort', 'Media')
Attribute = get_model('escort', 'Attribute')
AttributeValue = get_model('escort', 'AttributeValue')


class AttributeApiView(viewsets.ViewSet):
    """Get attribute options for medias
    Read only..."""
    lookup_field = 'uuid'
    permission_classes = (AllowAny,)
    parser_class = (FormParser, FileUploadParser, MultiPartParser,)
    permission_action = {
        # Disable update if not owner
        'update': [IsEntityOwnerOrReject],
        'partial_update': [IsEntityOwnerOrReject],
        'destroy': [IsEntityOwnerOrReject],
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

    def list(self, request, format=None):
        entity_object = None
        context = {'request': self.request}
        identifiers = request.GET.get('identifiers', None)
        entity_uuid = request.GET.get('entity_uuid', None)
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

        model_name = entity_model._meta.model_name  # ex: media, comment

        # Attributes
        if identifiers:
            identifiers = identifiers.split(',')

            # Get attribute by entity
            try:
                entity_uuid = UUID(entity_uuid)
            except ValueError:
                raise NotFound()

            try:
                entity_object = entity_model.objects.get(uuid=entity_uuid)
            except ObjectDoesNotExist:
                raise NotFound()

            # Call value each field
            try:
                queryset = Attribute.objects \
                    .prefetch_related('option_group', 'content_type') \
                    .select_related('option_group') \
                    .filter(
                        Q(content_type=entity_type),
                        Q(identifier__in=identifiers),
                        Q(**{'attributevalue__%s__isnull' % model_name: False}),
                        Q(**{'attributevalue__%s__uuid' % model_name: entity_uuid})) \
                    .distinct()
            except FieldError:
                raise NotFound()

            if queryset.exists():
                for qs in queryset:
                    identifiers.remove(qs.identifier)

                annotate = dict()
                for q in queryset:
                    field = 'value_' + q.field_type

                    if q.field_type == 'multi_option':
                        annotate[field] = F('attributevalue')
                    else:
                        annotate[field] = F('attributevalue__%s' % field)
                    annotate['value_uuid'] = F('attributevalue__uuid')

                # Call value each field
                queryset = queryset.annotate(**annotate)

            # Here we get all attributes
            # But filter by empty attributevalue
            queryset_all = Attribute.objects \
                .prefetch_related('option_group', 'content_type') \
                .select_related('option_group') \
                .filter(
                    content_type=entity_type,
                    identifier__in=identifiers) \
                .distinct()

            # Combine two or more queryset
            queryset = list(chain(queryset, queryset_all))

            # JSON Api
            serializer = AttributeSerializer(
                queryset, many=True, context=context)

            return Response(serializer.data, status=response_status.HTTP_200_OK)
        raise NotFound()

    # Update object attributes
    @method_decorator(csrf_protect)
    @method_decorator(never_cache)
    @transaction.atomic
    def update(self, request, uuid=None):
        """Update attribute values
        uuid used from entity object, not from attribute!
        So we can update multiple fields"""
        context = {'request': self.request}
        entity_index = request.data.get('entity_index', None)

        if entity_index is None or not uuid:
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

        # Udate attribute
        try:
            uuid = UUID(uuid)
        except ValueError:
            raise NotFound()

        try:
            entity_object = entity_model.objects.get(uuid=uuid)
        except ObjectDoesNotExist:
            raise NotFound()

        # Append file
        if request.FILES:
            setattr(request.data, 'files', request.FILES)

        # Update attribute
        update_attribute_values(
            entity_object, identifiers=None, values=request.data)

        # Get last inserted value
        attribute_value = AttributeValue.objects \
            .filter(object_id=entity_object.pk, content_type=entity_type) \
            .order_by('date_created') \
            .last()

        serializer = AttributeValueSerializer(
            attribute_value, many=False, context=context)
        return Response(serializer.data, status=response_status.HTTP_200_OK)

    # Update object attributes
    @method_decorator(csrf_protect)
    @method_decorator(never_cache)
    @transaction.atomic
    def partial_update(self, request, uuid=None):
        """
        {
            "entity_index": 0,
            "entity_uuid": "331ac501-805b-4243-95ae-c7ce87d8ae64",
            "value_uuid": "b6c537d0-2567-40a5-8a59-d8f4ee592f4a",
            "value": "My value"
        }

        If action update "value_uuid" required
        If action new, remove "value_uuid"
        """
        context = {'request': self.request}
        value = request.data.get('value', None)
        value_uuid = request.data.get('value_uuid', None)
        entity_uuid = request.data.get('entity_uuid', None)

        if not value:
            raise NotFound()

        try:
            uuid = UUID(uuid)
        except ValueError:
            raise NotFound()

        # Use for update onlye
        if value_uuid:
            try:
                value_uuid = UUID(value_uuid)
            except ValueError:
                raise NotFound()

        try:
            entity_uuid = UUID(entity_uuid)
        except ValueError:
            raise NotFound()

        # Updata action
        try:
            queryset = AttributeValue.objects.get(
                uuid=value_uuid,
                attribute__uuid=uuid)

            serializer = AttributeValueSerializer(
                instance=queryset,
                data=request.data,
                context=context,
                partial=True)
        except ObjectDoesNotExist:
            queryset = None

        # Create new
        if not queryset:
            request.data.update({'attribute_uuid': uuid})
            serializer = CreateAttributeValueSerializer(
                data=request.data, context=context)

        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response(serializer.data, status=response_status.HTTP_200_OK)
        return Response(serializer.errors, status=response_status.HTTP_400_BAD_REQUEST)

    # Delete...
    @method_decorator(csrf_protect)
    @method_decorator(never_cache)
    @transaction.atomic
    def destroy(self, request, uuid=None):
        """uuid used uuid from attribute value"""
        queryset = AttributeValue.objects.filter(uuid=uuid)
        if queryset.exists():
            queryset.delete()

        return Response(
            {'detail': _("Berhasil dihapus.")},
            status=response_status.HTTP_204_NO_CONTENT)


class ConstantApiView(viewsets.ViewSet):
    """Get constants Read only..."""
    lookup_field = 'uuid'
    permission_classes = (AllowAny,)

    def list(self, request, format=None):
        context = {'request': self.request}
        params = request.query_params
        constant = params.get('constant', None)
        response = list()

        if not constant:
            raise NotFound()

        if constant == 'publication':
            for key, value in PUBLICATION_CHOICES:
                for val in value:
                    response.append({
                        'uuid': val[0],
                        'label': str(val[1])
                    })

        return Response(response, status=response_status.HTTP_200_OK)
