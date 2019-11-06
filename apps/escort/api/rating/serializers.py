import uuid

from django.conf import settings
from django.db import transaction
from django.utils.translation import ugettext_lazy as _

# THIRD PARTY
from rest_framework import serializers
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import (
    NotFound, NotAcceptable, PermissionDenied)

# PERSON UTILS
from ....person.utils.auths import check_validation_passed

# PROJECT UTILS
from utils.validators import get_model

# LOCAL UTILS
from ...utils.constant import PENDING
from ...utils.generals import object_from_uuid
from ...utils.auths import CurrentPersonDefault

Media = get_model('escort', 'Media')
Rating = get_model('escort', 'Rating')


class RatingSerializer(serializers.ModelSerializer):
    """Rating model serializers"""
    url = serializers.HyperlinkedIdentityField(
        view_name='escorts:rating-detail', lookup_field='uuid', read_only=True)
    rater = serializers.CharField(source='rater.user.username')
    avatar = serializers.SerializerMethodField()

    class Meta:
        model = Rating
        exclude = ['id', 'media']

    def get_avatar(self, obj):
        request = self.context['request']
        if hasattr(obj, 'avatar'):
            if obj.avatar:
                return request.build_absolute_uri(settings.MEDIA_URL + obj.avatar)
            return None
        return None


class CreateRatingSerializer(serializers.ModelSerializer):
    """
    Create... Rating
    Format JSON;
    {
        "media": "23edfcca-b716-48ba-8aaa-0ae323b8bcbb",
        "score": 3,
        "description": "Lorem ipsum dolor..."
    }
    """
    rater = serializers.HiddenField(default=CurrentPersonDefault())

    class Meta:
        model = Rating
        fields = ['rater', 'uuid', 'score', 'description', 'media']
        read_only_fields = ['uuid']
        extra_kwargs = {
            'rater': {'write_only': True}
        }

    def __init__(self, **kwargs):
        data = kwargs['data']

        # Validate media defined
        try:
            media_uuid = data['media']
        except KeyError:
            raise NotFound()

        # Get object
        media_obj = object_from_uuid(
            self, Media, uuid_init=media_uuid)

        if media_obj:
            data['media'] = media_obj.pk
        super().__init__(**kwargs)

    @transaction.atomic
    def create(self, validated_data):
        try:
            request = self.context['request']
        except KeyError:
            raise NotAcceptable()

        # Append request to objects
        if request:
            setattr(Rating, 'request', request)

        person = getattr(request.user, 'person', None)
        if person is None:
            raise NotAcceptable()

        if not check_validation_passed(self, request=request):
            raise PermissionDenied(detail=_("Akun belum divalidasi."))

        # Create object, default status is PENDING
        return Rating.objects.create(**validated_data)
