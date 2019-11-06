from uuid import UUID

from django.db.models import (
    F, Q, Case, Value, BooleanField, OuterRef, Subquery)
from django.db import transaction
from django.utils.decorators import method_decorator
from django.core.exceptions import ObjectDoesNotExist
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie
from django.views.decorators.cache import never_cache
from django.contrib.contenttypes.models import ContentType

# THIRD PARTY
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status, viewsets
from rest_framework.pagination import PageNumberPagination
from rest_framework.exceptions import NotFound

# SERIALIZERS
from .serializers import RatingSerializer, CreateRatingSerializer

# MEDIA SERIALIZERS
from ..media.serializers import SingleMediaSerializer

# PERMISSIONS
from ..permissions import IsRaterOrReject

# PROJECT UTILS
from utils.validators import get_model

Media = get_model('escort', 'Media')
Rating = get_model('escort', 'Rating')

# Define to avoid used ...().paginate__
PAGINATOR = PageNumberPagination()


@method_decorator(ensure_csrf_cookie, name='dispatch')
class RatingApiView(viewsets.ViewSet):
    """Listen all rating action here..."""
    lookup_field = 'uuid'
    permission_classes = (AllowAny,)
    permission_action = {
        # Disable update if not owner
        'partial_update': [IsRaterOrReject]
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
        response['count'] = PAGINATOR.page.paginator.count
        response['navigate'] = {
            'previous': PAGINATOR.get_previous_link(),
            'next': PAGINATOR.get_next_link()
        }

        my_rating = kwargs.get('my_rating', None)
        if my_rating:
            response['my_rating'] = my_rating.data

        response['results'] = serializer.data
        return Response(response, status=status.HTTP_200_OK)

    def list(self, request, format=None):
        context = {'request': self.request}
        params = request.query_params
        media_uuid = params.get('media_uuid', None)
        my_rating_serializer = None

        if media_uuid:
            # The person
            person = getattr(self.request.user, 'person', None)

            try:
                media_uuid = UUID(media_uuid)
            except ValueError:
                raise NotFound()

            queryset = Rating.objects \
                .prefetch_related('media', 'rater', 'rater__user__person') \
                .select_related('media', 'rater', 'rater__user__person') \
                .filter(media__uuid=media_uuid)

            # Make sub-query for avatar only
            person_avatar = queryset.filter(
                rater__attribute_values__person=OuterRef('rater'),
                rater__attribute_values__attribute__identifier='avatar')

            # Append avatar
            queryset = queryset.annotate(
                avatar=Subquery(
                    person_avatar
                    .values('rater__attribute_values__value_image')))

            # Current user rating
            try:
                my_rating = queryset.get(rater=person)
            except ObjectDoesNotExist:
                my_rating = None

            if my_rating:
                my_rating_serializer = RatingSerializer(
                    my_rating, many=False, context=context)

            # Exclude current user rating from list
            queryset = queryset.exclude(rater=person)

            queryset_paginator = PAGINATOR.paginate_queryset(
                queryset, request)
            serializer = RatingSerializer(
                queryset_paginator, many=True, context=context)
            return self.get_response(
                serializer, my_rating=my_rating_serializer)
        raise NotFound()

    # Single item
    def retrieve(self, request, uuid=None, format=None):
        """ View as single object """
        context = {'request': self.request}
        raise NotFound()

    # Create object
    @method_decorator(csrf_protect)
    @method_decorator(never_cache)
    @transaction.atomic
    def create(self, request, format=None):
        """ Create single object """
        context = {'request': self.request}
        serializer = CreateRatingSerializer(data=request.data, context=context)
        if serializer.is_valid(raise_exception=True):
            media = serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # Update item data
    @method_decorator(csrf_protect)
    @method_decorator(never_cache)
    @transaction.atomic
    def partial_update(self, request, uuid=None, format=None):
        """Update a item... """
        context = {'request': self.request}
        rating_uuid = uuid
        person = None

        try:
            rating_uuid = UUID(rating_uuid)
        except ValueError:
            raise NotFound()

        if hasattr(self.request.user, 'person'):
            person = self.request.user.person

        try:
            queryset = Rating.objects.get(
                uuid=rating_uuid,
                rater=person)
        except ObjectDoesNotExist:
            raise NotFound()

        serializer = CreateRatingSerializer(
            instance=queryset,
            data=request.data,
            context=context,
            partial=True)

        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
