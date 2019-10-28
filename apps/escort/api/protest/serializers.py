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
from ....person.utils.auths import check_verified_email, check_verified_phone

# PROJECT UTILS
from utils.validators import get_model


# LOCAL UTILS
from ...utils.constant import DRAFT, PENDING
from ...utils.generals import object_from_uuid
from ...utils.auths import CurrentPersonDefault

Media = get_model('escort', 'Media')
Protest = get_model('escort', 'Protest')


class ProtestSerializer(serializers.ModelSerializer):
    """Protest model serializers"""
    url = serializers.HyperlinkedIdentityField(
        view_name='escorts:protest-detail', lookup_field='uuid', read_only=True)
    protester = serializers.CharField(source='protester.user.username')
    avatar = serializers.SerializerMethodField()
    media = serializers.UUIDField(source='media.uuid')
    media_label = serializers.UUIDField(source='media.label')

    class Meta:
        model = Protest
        exclude = ['id']

    def get_avatar(self, obj):
        request = self.context['request']

        if hasattr(obj, 'avatar'):
            if obj.avatar:
                return request \
                    .build_absolute_uri(settings.MEDIA_URL + obj.avatar)
            return None
        return None


class SingleProtestSerializer(serializers.ModelSerializer):
    protester = serializers.CharField(source='protester.user.username')
    avatar = serializers.SerializerMethodField()
    status_label = serializers.CharField(source='get_status_display')
    attribute_values = serializers.SerializerMethodField()
    ownership = serializers.BooleanField()
    media = serializers.UUIDField(source='media.uuid')
    media_label = serializers.CharField(source='media.label')
    thumbing = serializers.BooleanField()
    thumbing_uuid = serializers.UUIDField()

    class Meta:
        model = Protest
        exclude = ['id']

    def get_avatar(self, obj):
        request = self.context['request']

        if hasattr(obj, 'avatar'):
            if obj.avatar:
                return request \
                    .build_absolute_uri(settings.MEDIA_URL + obj.avatar)
            return None
        return None

    def get_attribute_values(self, obj):
        values_dict = {}
        request = self.context['request']

        # Has attribute
        if hasattr(obj, 'attribute_values'):
            values = obj.attribute_values \
                .prefetch_related('attribute') \
                .select_related('attribute') \
                .all()

            if values.exists():
                for value in values:
                    type = value.attribute.type
                    identifier = value.attribute.identifier
                    name = 'value_%s' % type
                    content = getattr(value, name)

                    # Has value
                    if content:
                        # Image and file has url
                        if type == 'image' or type == 'file':
                            url = content.url
                            content = request.build_absolute_uri(url)

                        if type == 'option':
                            content = content.option

                        if type == 'multi_option':
                            option = content \
                                .prefetch_related('attributevalue') \
                                .select_related('attributevalue') \
                                .defer('attributevalue') \
                                .values('option')
                            content = option
                        values_dict[identifier] = content
                return values_dict
            return None
        return None


class CreateProtestSerializer(serializers.ModelSerializer):
    """
    Create...
    Format JSON;
    {
        "label": "Pelaporan",
        "description": "Saya laporkan ini...",
        "media_uuid": "4e43e050-6cc8-45c1-af2d-cddbd67ff3b3",
        "purpose": 1
    }
    """
    protester = serializers.HiddenField(default=CurrentPersonDefault())

    class Meta:
        model = Protest
        fields = ['protester', 'uuid', 'label', 'description',
                  'media', 'purpose']
        read_only_fields = ['uuid']
        extra_kwargs = {
            'protester': {'write_only': True}
        }

    def __init__(self, **kwargs):
        data = kwargs['data']

        # Validate media defined
        try:
            media_uuid = kwargs['data']['media_uuid']
        except KeyError:
            raise NotFound()

        # Get object
        media_obj = object_from_uuid(
            self, Media,
            uuid_init=media_uuid)

        if media_obj:
            kwargs['data']['media'] = media_obj.pk
        super().__init__(**kwargs)

    @transaction.atomic
    def update(self, instance, validated_data):
        try:
            request = self.context['request']
        except KeyError:
            raise NotAcceptable()

        # Updata object
        instance.label = validated_data.get('label', instance.label)
        instance.description = validated_data.get(
            'description',
            instance.description)
        instance.purpose = validated_data.get('purpose', instance.purpose)

        if instance.status == DRAFT:
            instance.status = PENDING

        instance.save()
        return instance

    @transaction.atomic
    def create(self, validated_data):
        try:
            request = self.context['request']
        except KeyError:
            raise NotAcceptable()

        # Append request to objects
        if request:
            setattr(Protest, 'request', request)

        person = getattr(request.user, 'person', None)
        if person is None:
            raise NotAcceptable()

        is_verified_phone = check_verified_phone(self, person=person)
        if is_verified_phone is False:
            raise PermissionDenied(detail=_("Nomor ponsel belum diverifikasi."))

        is_verified_email = check_verified_email(self, person=person)
        if is_verified_email is False:
            raise PermissionDenied(detail=_("Alamat email belum diverifikasi."))

        # Create object, default status is DRAFT
        return Protest.objects.create(status=DRAFT, **validated_data)
