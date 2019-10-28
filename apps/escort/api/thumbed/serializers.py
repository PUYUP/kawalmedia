import uuid

from django.db import transaction
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import ugettext_lazy as _

# THIRD PARTY
from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.exceptions import (
    NotFound, NotAcceptable, PermissionDenied)

# PROJECT UTILS
from utils.validators import get_model

# PERSON UTILS
from ....person.utils.auths import check_verified_email, check_verified_phone

# LOCAL UTILS
from ...utils.generals import object_from_uuid
from ...utils.auths import CurrentPersonDefault

# LOCAL MODELS
from ...models.models import __all__ as model_index

Thumbed = get_model('escort', 'Thumbed')
Protest = get_model('escort', 'Protest')


class ThumbedSerializer(serializers.ModelSerializer):
    """Serialize Thumbed"""
    thumber = serializers.SerializerMethodField()

    class Meta:
        model = Thumbed
        fields = '__all__'

    def get_thumber(self, obj):
        thumber = getattr(obj, 'thumber', None)
        if thumber:
            return thumber.uuid
        return None


class CreateThumbedSerializer(serializers.ModelSerializer):
    """Create Thumbed"""
    thumber = serializers.HiddenField(default=CurrentPersonDefault())

    class Meta:
        model = Thumbed
        exclude = ('date_created', 'date_updated',)
        extra_kwargs = {
            'thumber': {'write_only': True}
        }

    def __init__(self, **kwargs):
        data = kwargs['data']

        # Validate entity_uuid
        try:
            entity_uuid = kwargs['data']['entity_uuid']
        except KeyError:
            raise NotFound()

        # Validate entity_index
        try:
            entity_index = kwargs['data']['entity_index']
        except KeyError:
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

        # Get object
        entity_object = object_from_uuid(
            self, entity_model,
            uuid_init=entity_uuid)

        if entity_object:
            entity_type = ContentType.objects.get_for_model(entity_object)

            kwargs['data']['object_id'] = entity_object.pk
            kwargs['data']['content_type'] = entity_type.pk
        super().__init__(**kwargs)

    @transaction.atomic
    def create(self, validated_data):
        try:
            request = self.context['request']
        except KeyError:
            raise NotAcceptable()

        # Append request to objects
        if request:
            setattr(Thumbed, 'request', request)

        person = getattr(request.user, 'person', None)
        if person is None:
            raise NotAcceptable()

        is_verified_phone = check_verified_phone(self, person=person)
        if is_verified_phone is False:
            raise PermissionDenied(detail=_("Nomor ponsel belum diverifikasi."))

        is_verified_email = check_verified_email(self, person=person)
        if is_verified_email is False:
            raise PermissionDenied(detail=_("Alamat email belum diverifikasi."))

        return Thumbed.objects.create(**validated_data)

    @transaction.atomic
    def update(self, instance, validated_data):
        try:
            request = self.context['request']
        except KeyError:
            raise NotAcceptable()

        # Updata object
        thumbing = validated_data.get('thumbing', instance.thumbing)

        # Only accept if 0 or 1
        # 0 = thumb up
        # 1 = thumb down
        if thumbing == 0 or thumbing == 1:
            instance.thumbing = thumbing
            instance.save()

        return instance
