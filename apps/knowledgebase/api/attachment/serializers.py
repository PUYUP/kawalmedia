import uuid

from django.db import transaction
from django.contrib.contenttypes.models import ContentType

# THIRD PARTY
from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.exceptions import (
    NotFound, NotAcceptable, PermissionDenied)

# PROJECT UTILS
from utils.validators import get_model

# LOCAL UTILS
from ...utils.generals import object_from_uuid
from ...utils.auths import CurrentPersonDefault

# LOCAL MODELS
from ...models.models import __all__ as model_index

Attachment = get_model('knowledgebase', 'Attachment')


class AttachmentSerializer(serializers.ModelSerializer):
    """Serialize Attachment"""
    uploader = serializers.SerializerMethodField()

    class Meta:
        model = Attachment
        fields = '__all__'

    def get_uploader(self, obj):
        uploader = getattr(obj, 'uploader', None)
        if uploader:
            return uploader.uuid
        return None


class CreateAttachmentSerializer(serializers.ModelSerializer):
    """Create Attachment"""
    uploader = serializers.HiddenField(default=CurrentPersonDefault())

    class Meta:
        model = Attachment
        exclude = ('date_created', 'date_updated',)
        extra_kwargs = {
            'uploader': {'write_only': True}
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
            entity_model = get_model('knowledgebase', entity_class)
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
        return Attachment.objects.create(**validated_data)
