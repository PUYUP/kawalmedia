from uuid import UUID
from itertools import chain

from django.db.models import F, Subquery, OuterRef
from django.db import transaction
from django.utils.translation import ugettext_lazy as _
from django.utils.decorators import method_decorator
from django.core.exceptions import ObjectDoesNotExist
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie
from django.views.decorators.cache import never_cache
from django.contrib.contenttypes.models import ContentType

# THIRD PARTY
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.parsers import (
    FormParser, FileUploadParser, MultiPartParser)
from rest_framework import status as response_status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, NotAcceptable

# SERIALIZERS
from .serializers import AttributeSerializer, AttributeValueSerializer

# PERMISSIONS
from ..permissions import IsOwnerOrReject, IsEntityOwnerOrReject

# LOCAL UTILS
from ...utils.attributes import update_attribute_values

# GET MODELS FROM GLOBAL UTILS
from utils.validators import get_model

Attribute = get_model('person', 'Attribute')
AttributeValue = get_model('person', 'AttributeValue')


class AttributeApiView(viewsets.ViewSet):
    """ Get attribute options for persons
    Read only... """
    lookup_field = 'uuid'
    permission_classes = (IsAuthenticated,)
    parser_class = (FormParser, FileUploadParser, MultiPartParser,)
    permission_action = {
        # Disable update if not owner
        'update': [IsOwnerOrReject],
        'partial_update': [IsOwnerOrReject],
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
        context = {'request': self.request}
        identifiers = request.GET.get('identifiers', None)

        # Attributes
        if hasattr(request.user, 'person') and identifiers:
            person = getattr(request.user, 'person', None)
            identifiers = identifiers.split(',')

            # ContentType berdasarkan entity (model)
            entity_type = ContentType.objects.get_for_model(person)

            # Get roles from person
            roles = person.roles.filter(is_active=True) \
                .values_list('id', flat=True)

            # Get attributes by roles
            queryset = Attribute.objects \
                .prefetch_related('option_group', 'content_type', 'roles') \
                .select_related('option_group') \
                .filter(
                    content_type=entity_type,
                    roles__in=roles,
                    identifier__in=identifiers,
                    attributevalue__object_id=person.pk) \
                .distinct()

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
                .prefetch_related('option_group', 'content_type', 'roles') \
                .select_related('option_group') \
                .filter(
                    content_type=entity_type,
                    roles__in=roles,
                    identifier__in=identifiers,
                    secured=False) \
                .distinct()

            # Combine two or more queryset
            queryset = list(chain(queryset, queryset_all))

            # JSON Api
            serializer = AttributeSerializer(
                queryset, many=True, context=context)

            return Response(serializer.data, status=response_status.HTTP_200_OK)
        raise NotAcceptable(detail=_("Data tidak valid."))

    # Update person attributes
    @method_decorator(csrf_protect)
    @transaction.atomic
    def update(self, request, uuid=None):
        """Update attribute values
        UUID used is Person identifier"""
        context = {'request': self.request}

        if type(uuid) is not UUID:
            try:
                uuid = UUID(uuid)
            except ValueError:
                raise NotFound()

        person = getattr(request.user, 'person', None)
        if person and request.data:
            # Append file
            if request.FILES:
                setattr(request.data, 'files', request.FILES)

            # Update attribute
            update_attribute_values(
                person, identifiers=None, values=request.data)

            # Get last inserted value
            entity_type = ContentType.objects.get_for_model(person)
            attribute_value = AttributeValue.objects \
                .filter(object_id=person.pk, content_type=entity_type) \
                .order_by('date_created') \
                .last()

            serializer = AttributeValueSerializer(
                attribute_value, many=False, context=context)

            return Response(serializer.data, status=response_status.HTTP_200_OK)
        raise NotAcceptable()

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
