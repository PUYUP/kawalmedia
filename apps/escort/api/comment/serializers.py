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
from ...utils.constant import DRAFT, PENDING
from ...utils.generals import object_from_uuid
from ...utils.auths import CurrentPersonDefault

Person = get_model('person', 'Person')
Protest = get_model('escort', 'Protest')
Comment = get_model('escort', 'Comment')
Notification = get_model('notice', 'Notification')


class CommentSerializer(serializers.ModelSerializer):
    """Protest model serializers"""
    url = serializers.HyperlinkedIdentityField(
        view_name='escorts:comment-detail', lookup_field='uuid', read_only=True)
    commenter = serializers.CharField(source='commenter.user.username')
    commenter_uuid = serializers.CharField(source='commenter.uuid')
    reply_for_person_name = serializers.SerializerMethodField()
    ownership = serializers.BooleanField()
    avatar = serializers.SerializerMethodField()
    protest = serializers.UUIDField(source='protest.uuid')
    protest_label = serializers.UUIDField(source='protest.label')

    class Meta:
        model = Comment
        exclude = ['id']

    def get_reply_for_person_name(self, obj):
        reply_for_person = getattr(obj, 'reply_for_person', None)
        if reply_for_person:
            return reply_for_person.user.username
        return None

    def get_avatar(self, obj):
        request = self.context['request']

        if hasattr(obj, 'avatar'):
            if obj.avatar:
                return request \
                    .build_absolute_uri(settings.MEDIA_URL + obj.avatar)
            return None
        return None


class SingleCommentSerializer(serializers.ModelSerializer):
    commenter = serializers.CharField(source='commenter.user.username')
    commenter_uuid = serializers.CharField(source='commenter.uuid')
    reply_for_person_name = serializers.SerializerMethodField()
    avatar = serializers.SerializerMethodField()
    ownership = serializers.BooleanField()
    protest = serializers.UUIDField(source='protest.uuid')
    protest_label = serializers.CharField(source='protest.label')

    class Meta:
        model = Comment
        exclude = ['id']

    def get_reply_for_person_name(self, obj):
        reply_for_person = getattr(obj, 'reply_for_person', None)
        if reply_for_person:
            return reply_for_person.user.username
        return None

    def get_avatar(self, obj):
        request = self.context['request']

        if hasattr(obj, 'avatar'):
            if obj.avatar:
                return request \
                    .build_absolute_uri(settings.MEDIA_URL + obj.avatar)
            return None
        return None


class CreateCommentSerializer(serializers.ModelSerializer):
    """
    Create...
    Format JSON;
    {
        "description": "Saya laporkan ini...",
        "protest_uuid": "4e43e050-6cc8-45c1-af2d-cddbd67ff3b3",
        "parent": None,
        "reply_to_comment": "4e43e050-6cc8-45c1-af2d-cddbd67ff3b3",
        "reply_for_person": "4e43e050-6cc8-45c1-af2d-cddbd67ff3b3",
    }
    """
    commenter = serializers.HiddenField(default=CurrentPersonDefault())

    class Meta:
        model = Comment
        fields = ['commenter', 'uuid', 'description', 'protest',
                  'parent', 'reply_to_comment', 'reply_for_person']
        read_only_fields = ['uuid']
        extra_kwargs = {
            'commenter': {'write_only': True}
        }

    def __init__(self, **kwargs):
        data = kwargs['data']

        # Validate protest defined
        try:
            protest_uuid = data['protest_uuid']
        except KeyError:
            raise NotFound()

        # Get object
        protest_obj = object_from_uuid(
            self, Protest,
            uuid_init=protest_uuid)

        if protest_obj:
            data['protest'] = protest_obj.pk

        # Validate self, this use if reply to
        try:
            comment_uuid = data['parent_uuid']
        except KeyError:
            comment_uuid = None

        # Get object
        if comment_uuid:
            comment_obj = object_from_uuid(
                self, Comment,
                uuid_init=comment_uuid)

            if comment_obj:
                data['parent'] = comment_obj.pk

        # Validate reply_to_comment
        try:
            reply_to_comment_uuid = data['reply_to_comment']
        except KeyError:
            reply_to_comment_uuid = None

        # Get object
        if reply_to_comment_uuid:
            reply_to_comment_obj = object_from_uuid(
                self, Comment,
                uuid_init=reply_to_comment_uuid)

            if reply_to_comment_obj:
                data['reply_to_comment'] = reply_to_comment_obj.pk

        # Validate reply_for_person
        try:
            reply_for_person_uuid = data['reply_for_person']
        except KeyError:
            reply_for_person_uuid = None

        # Get object
        if reply_for_person_uuid:
            reply_for_person_obj = object_from_uuid(
                self, Person,
                uuid_init=reply_for_person_uuid)

            if reply_for_person_obj:
                data['reply_for_person'] = reply_for_person_obj.pk

        super().__init__(**kwargs)

    @transaction.atomic
    def create(self, validated_data):
        try:
            request = self.context['request']
        except KeyError:
            raise NotAcceptable()

        # Append request to objects
        if request:
            setattr(Comment, 'request', request)

        person = getattr(request.user, 'person', None)
        if not person:
            raise NotAcceptable()

        if not check_validation_passed(self, request=request):
            raise PermissionDenied(detail=_("Akun belum divalidasi."))

        # Create object, default status is DRAFT
        return Comment.objects.create(**validated_data)

    @transaction.atomic
    def update(self, instance, validated_data):
        try:
            request = self.context['request']
        except KeyError:
            raise NotAcceptable()

        # Updata object
        instance.description = validated_data.get(
            'description',
            instance.description)

        instance.save()
        return instance
