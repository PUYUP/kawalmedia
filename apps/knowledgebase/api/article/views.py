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
    ArticleSerializer, SingleArticleSerializer)

# PROJECT UTILS
from utils.validators import get_model

# LOCAL UTILS
from ...utils.constant import PUBLISHED

Article = get_model('knowledgebase', 'Article')

# Define to avoid used ...().paginate__
PAGINATOR = PageNumberPagination()


class ArticleApiView(viewsets.ViewSet):
    """Listen all protest action here..."""
    lookup_field = 'uuid'
    permission_classes = (AllowAny,)

    # Get a objects
    def get_object(self, uuid=None, *agrs, **kwargs):
        limit = kwargs.get('limit', None)
        ids = kwargs.get('ids', None)

        try:
            if uuid:
                if type(uuid) is not UUID:
                    try:
                        uuid = UUID(uuid)
                    except ValueError:
                        raise NotFound()

                return Article.objects \
                    .prefetch_related('writer', 'writer__user__person') \
                    .select_related('writer', 'writer__user__person') \
                    .get(uuid=uuid, status=PUBLISHED)

            # List objects
            queryset = Article.objects \
                .prefetch_related('writer', 'writer__user__person') \
                .select_related('writer', 'writer__user__person') \
                .filter(status=PUBLISHED)

            # Get by ids
            if ids:
                list_ids = ids.split(',')
                queryset = queryset.filter(pk__in=list_ids)

            # Get only X items
            if limit:
                queryset = queryset[:int(limit)]

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
        limit = params.get('limit', None)
        ids = params.get('ids', None)

        # Get protest objects...
        queryset = self.get_object(limit=limit, ids=ids)
        queryset_paginator = PAGINATOR.paginate_queryset(
            queryset, request)
        serializer = ArticleSerializer(
            queryset_paginator, many=True, context=context)
        return self.get_response(serializer)

    # Single item
    def retrieve(self, request, uuid=None, format=None):
        """ View as single object """
        context = {'request': self.request}
        queryset = self.get_object(uuid)
        serializer = SingleArticleSerializer(
            queryset, many=False, context=context)
        return Response(serializer.data, status=response_status.HTTP_200_OK)
