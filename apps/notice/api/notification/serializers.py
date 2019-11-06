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

# PROJECT UTILS
from utils.validators import get_model

Notification = get_model('notice', 'Notification')


class NotificationSerializer(serializers.ModelSerializer):
    """Notification model serializers"""
    content = serializers.SerializerMethodField()
    content_uuid = serializers.UUIDField(format='hex_verbose')
    content_notified = serializers.SerializerMethodField()
    content_notified_uuid = serializers.UUIDField(format='hex_verbose')
    content_source_uuid = serializers.UUIDField(format='hex_verbose')
    content_parent_uuid = serializers.UUIDField(format='hex_verbose')
    content_source_type = serializers.SerializerMethodField()
    actor = serializers.CharField()
    verb_label = serializers.CharField(source='get_verb_display')

    class Meta:
        model = Notification
        exclude = ['id', 'content_notified_type', 'content_type',
                   'content_notified_id', 'content_id', 'content_source_id']

    def get_content(self, obj):
        if obj.content:
            return obj.content[:50] + '...'
        return None

    def get_content_notified(self, obj):
        if obj.content_notified:
            return obj.content_notified[:50] + '...'
        return None

    def get_content_source_type(self, obj):
        if obj.content_source_type:
            return obj.content_source_type.model
        return None


class CreateNotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ['uuid', 'unread']

    @transaction.atomic
    def update(self, instance, validated_data):
        try:
            request = self.context['request']
        except KeyError:
            raise NotAcceptable()

        # Updata object
        instance.unread = False

        instance.save()
        return instance
