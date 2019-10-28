from uuid import UUID

from django.http import Http404
from django.db.models import F, Q
from django.db import transaction
from django.utils.translation import ugettext_lazy as _
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
from django.contrib.contenttypes.models import ContentType

# THIRD PARTY
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.parsers import (
    FormParser, FileUploadParser, MultiPartParser)
from rest_framework import status, viewsets
from rest_framework.exceptions import NotFound, NotAcceptable

# SERIALIZERS
from .serializers import AttributeSerializer

# PERMISSIONS
from ..permissions import IsOwnerOrReject, IsCreatorOrReject

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


class OptionApiView(viewsets.ViewSet):
    """Get attribute options for medias
    Read only..."""
    lookup_field = 'uuid'
    permission_classes = (AllowAny,)
    parser_class = (FormParser, FileUploadParser, MultiPartParser,)
    permission_action = {
        # Disable update if not owner
        'update': [IsOwnerOrReject],
        'partial_update': [IsOwnerOrReject]
    }

    def list(self, request, format=None):
        entity_object = None
        response = {}
        context = {'request': self.request}
        identifiers = request.GET.get('identifiers', None)
        entity_uuid = request.GET.get('entity_uuid', None)
        entity_index = request.GET.get('entity_index', None)

        if entity_index is None:
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
            if entity_uuid:
                try:
                    entity_uuid = UUID(entity_uuid)
                    entity_object = entity_model.objects.get(uuid=entity_uuid)
                except ValueError:
                    raise NotFound()
            else:
                entity_uuid = None

            # Call value each field
            queryset = Attribute.objects \
                .filter(
                    Q(content_type=entity_type),
                    Q(identifier__in=identifiers),
                    Q(**{'attributevalue__%s__isnull' % model_name: False}),
                    Q(**{'attributevalue__%s__uuid' % model_name: entity_uuid})) \
                .prefetch_related('option_group') \
                .select_related('option_group') \
                .distinct()

            if queryset.exists():
                for qs in queryset:
                    identifiers.remove(qs.identifier)

                annotate = {}
                for q in queryset:
                    field = 'value_' + q.type
                    if q.type == 'multi_option':
                        annotate[field] = F('attributevalue')
                    else:
                        annotate[field] = F('attributevalue__%s' % field)

                # Call value each field
                queryset = queryset.annotate(**annotate)

            # Here we get all attributes
            # But filter by empty attributevalue
            queryset_all = Attribute.objects \
                .filter(
                    content_type=entity_type,
                    identifier__in=identifiers) \
                .prefetch_related('option_group') \
                .select_related('option_group') \
                .distinct()

            # Combine two or more queryset
            queryset = queryset | queryset_all

            # JSON Api
            serializer = AttributeSerializer(
                queryset, many=True, context=context)

            # Models object value
            # Only if Media
            if model_name == 'media':
                basics = [
                    {
                        'value': {
                            'field': 'value_text',
                            'object': entity_object.label if entity_object else None,
                            'object_print': None,
                            'required': True,
                        },
                        'type': 'text',
                        'identifier': 'label',
                        'label': _("Nama Media"),
                        'option_group': None,
                        'secured': False,
                        'minlength': 3,
                    },
                    {
                        'value': {
                            'field': 'value_option',
                            'object': entity_object.publication if entity_object else None,
                            'object_print': None,
                            'required': True,
                        },
                        'type': 'option',
                        'identifier': 'publication',
                        'label': _("Jenis Publikasi"),
                        'option_group': None,
                        'secured': False,
                        'minlength': 3,
                    },
                ]
                response['basics'] = basics

            response['attributes'] = serializer.data
            return Response(response, status=status.HTTP_200_OK)
        raise NotFound()

    # Update object attributes
    @method_decorator(csrf_protect)
    @transaction.atomic
    def update(self, request, uuid=None):
        """ Update attribute values """
        response = {}
        action = request.data.get('action', None)
        entity_index = request.data.get('entity_index', None)

        if entity_index is None:
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

        if not action:
            raise NotAcceptable(detail=_("Data invalid."))

        # Udate attribute
        if action == 'update_attribute':
            if uuid:
                try:
                    uuid = UUID(uuid)
                    entity_object = entity_model.objects.get(uuid=uuid)
                except ValueError:
                    raise NotFound()

            # Media object
            if model_name == 'media':
                # Only creator can edit attributes
                if entity_object.creator != request.user.person:
                    raise NotAcceptable

                if 'label' in request.data or 'publication' in request.data:
                    if 'label' in request.data:
                        label = request.data.pop('label')
                        entity_object.label = label

                    if 'publication' in request.data:
                        publication = request.data.pop('publication')
                        entity_object.publication = publication
                    entity_object.save()
            else:
                raise NotFound()

            # Append file
            if request.FILES:
                setattr(request.data, 'files', request.FILES)

            # Update attribute
            update_attribute_values(
                entity_object, identifiers=None, values=request.data)
            response['uuid'] = uuid
        return Response(response, status=status.HTTP_200_OK)


class ConstantApiView(viewsets.ViewSet):
    """Get constants Read only..."""
    lookup_field = 'uuid'
    permission_classes = (AllowAny,)

    def list(self, request, format=None):
        context = {'request': self.request}
        params = request.query_params
        constant = params.get('constant', None)
        response = []

        if not constant:
            raise NotFound()

        if constant == 'publication':
            for key, value in PUBLICATION_CHOICES:
                for val in value:
                    response.append({
                        'uuid': val[0],
                        'label': str(val[1])
                    })

        return Response(response, status=status.HTTP_200_OK)
