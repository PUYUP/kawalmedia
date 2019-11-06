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
from .serializers import (
    ValidationSerializer, CreateValidationValueSerializer,
    ValidationValueSerializer)

# PERMISSIONS
from ..permissions import IsOwnerOrReject

# LOCAL UTILS
from ...utils.validations import update_validation_values

# GET MODELS FROM GLOBAL UTILS
from utils.validators import get_model

Validation = get_model('person', 'Validation')
ValidationValue = get_model('person', 'ValidationValue')


class ValidationApiView(viewsets.ViewSet):
    """ Get validation for persons
    Read only... """
    lookup_field = 'uuid'
    permission_classes = (IsAuthenticated,)
    parser_class = (FormParser, FileUploadParser, MultiPartParser,)
    permission_action = {
        # Disable update if not owner
        # 'update': [IsOwnerOrReject],
        # 'partial_update': [IsOwnerOrReject]
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
        person = getattr(request.user, 'person', None)

        # Validations
        if person and identifiers:
            identifiers = identifiers.split(',')

            # ContentType berdasarkan entity (model)
            entity_type = ContentType.objects.get_for_model(person)

            # Get roles from person
            roles = person.roles.filter(is_active=True) \
                .values_list('id', flat=True)

            # Get attributes by roles
            queryset = Validation.objects \
                .prefetch_related('content_type', 'roles') \
                .filter(
                    content_type=entity_type,
                    roles__in=roles,
                    identifier__in=identifiers,
                    validationvalue__object_id=person.pk) \
                .distinct()

            if queryset.exists():
                for qs in queryset:
                    identifiers.remove(qs.identifier)

                annotate = dict()
                for q in queryset:
                    field = 'value_' + q.field_type

                    if q.field_type == 'multi_option':
                        annotate[field] = F('validationvalue')
                    else:
                        annotate[field] = F('validationvalue__%s' % field)

                    annotate['value_uuid'] = F('validationvalue__uuid')
                    annotate['verified'] = F('validationvalue__verified')

                # Call value each field
                queryset = queryset.annotate(**annotate)

            # Here we get all attributes
            # But filter by empty validationvalue
            queryset_all = Validation.objects \
                .prefetch_related('content_type', 'roles') \
                .filter(
                    content_type=entity_type,
                    roles__in=roles,
                    identifier__in=identifiers) \
                .distinct()

            # Combine two or more queryset
            queryset = list(chain(queryset, queryset_all))

            # JSON Api
            serializer = ValidationSerializer(
                queryset, many=True, context=context)

            return Response(serializer.data, status=response_status.HTTP_200_OK)
        raise NotAcceptable(detail=_("Data tidak valid."))

    # Update person validations
    @method_decorator(csrf_protect)
    @method_decorator(never_cache)
    @transaction.atomic
    def update(self, request, uuid=None):
        """Update validation values
        UUID used is Person identifier"""
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

            # Update validation
            update_validation_values(
                person, identifiers=None, values=request.data)
            return Response(status=response_status.HTTP_200_OK)
        raise NotAcceptable()

    # Update object validations
    @method_decorator(csrf_protect)
    @method_decorator(never_cache)
    @transaction.atomic
    def partial_update(self, request, uuid=None):
        """
        {
            "value_uuid": "b6c537d0-2567-40a5-8a59-d8f4ee592f4a",
            "value": "My value"
        }

        If action update "value_uuid" required
        If action new, remove "value_uuid"
        """
        context = {'request': self.request}
        value = request.data.get('value', None)
        value_uuid = request.data.get('value_uuid', None)

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

        # Updata action
        try:
            queryset = ValidationValue.objects.get(
                uuid=value_uuid,
                validation__uuid=uuid)

            serializer = ValidationValueSerializer(
                instance=queryset,
                data=request.data,
                context=context,
                partial=True)
        except ObjectDoesNotExist:
            queryset = None

        # Create new
        if not queryset:
            request.data.update({'validation_uuid': uuid})
            serializer = CreateValidationValueSerializer(
                data=request.data, context=context)

        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response(serializer.data, status=response_status.HTTP_200_OK)
        return Response(serializer.errors, status=response_status.HTTP_400_BAD_REQUEST)
