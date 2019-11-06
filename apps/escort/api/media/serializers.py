import uuid

from django.db import transaction
from django.db.models import Q, F, Count, Avg, FloatField
from django.utils.translation import ugettext_lazy as _
from django.utils.text import Truncator, slugify

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
from ...utils.constant import PENDING, SCORE_CHOICES
from ...utils.generals import object_from_uuid
from ...utils.attributes import update_attribute_values
from ...utils.auths import CurrentPersonDefault

Media = get_model('escort', 'Media')
AttributeValue = get_model('escort', 'AttributeValue')


class MediaSerializer(serializers.ModelSerializer):
    """Media model serializers"""
    url = serializers.HyperlinkedIdentityField(
        view_name='escorts:media-detail', lookup_field='uuid', read_only=True)
    status_label = serializers.CharField(source='get_status_display')
    creator = serializers.CharField(source='creator.user.username')
    attribute_values = serializers.SerializerMethodField()
    rating_average = serializers.CharField()

    class Meta:
        model = Media
        fields = ['uuid', 'url', 'creator', 'attribute_values', 'label',
                  'protest_count', 'comment_count', 'rating_count',
                  'status', 'status_label', 'rating_average']

    def get_attribute_values(self, obj):
        values_dict = dict()
        request = self.context['request']
        identifiers = ['logo', 'description']

        values = obj.attribute_values \
            .prefetch_related('attribute', 'content_type') \
            .select_related('attribute', 'content_type') \
            .filter(attribute__identifier__in=identifiers)

        if values.exists():
            for value in values:
                type = value.attribute.field_type
                identifier = value.attribute.identifier
                name = 'value_%s' % type
                content = getattr(value, name)

                if content:
                    # Image and file has url
                    if type == 'image' or type == 'file':
                        url = content.url
                        content = request.build_absolute_uri(url)

                    # Trucante richtext
                    if type == 'richtext':
                        content = Truncator(content).words(5)
                    values_dict[identifier] = content
            return values_dict
        return None


class SingleMediaSerializer(serializers.ModelSerializer):
    creator = serializers.CharField(source='creator.user.username')
    status_label = serializers.CharField(source='get_status_display')
    status_description = serializers.SerializerMethodField()
    attribute_values = serializers.SerializerMethodField()
    ownership = serializers.BooleanField()
    ratings = serializers.SerializerMethodField()

    """Single media..."""
    class Meta:
        model = Media
        exclude = ['id']

    def get_attribute_values(self, obj):
        values_dict = dict()
        request = self.context['request']
        values = obj.attribute_values \
            .prefetch_related('attribute', 'content_type') \
            .select_related('attribute', 'content_type') \
            .all()

        if values.exists():
            for value in values:
                field_type = value.attribute.field_type
                identifier = value.attribute.identifier
                name = 'value_%s' % field_type
                content = getattr(value, name)

                # Has value
                if content:
                    # Image and file has url
                    if field_type == 'image' or field_type == 'file':
                        url = content.url
                        content = request.build_absolute_uri(url)

                    if field_type == 'option':
                        content = content.option

                    if field_type == 'multi_option':
                        option = content \
                            .prefetch_related('attributevalue') \
                            .select_related('attributevalue') \
                            .defer('attributevalue') \
                            .values('option')
                        content = option
                    values_dict[identifier] = {
                        'uuid': value.uuid,
                        'object': content,
                    }
            return values_dict
        return None

    def get_ratings(self, obj):
        scores = dict()
        for sc in SCORE_CHOICES:
            val = sc[0]
            key = slugify(sc[1])
            key = key.replace('-', '_')
            key = '%s' % (val)
            agrt = {key: Count('score', filter=Q(score__iexact=val))}
            scores.update(agrt)

        ratings = obj.rating_set \
            .aggregate(
                **scores,
                score_avg=Avg(F('score'), output_field=FloatField()))
        return ratings

    def get_status_description(self, obj):
        log = obj.status_log.last()
        if log:
            return log.description


class CreateMediaSerializer(serializers.ModelSerializer):
    """
    Create...
    Format JSON;
    {
        "label": "Jayakah",
        "publication": "1"
    }
    """
    creator = serializers.HiddenField(default=CurrentPersonDefault())

    class Meta:
        model = Media
        fields = ('creator', 'uuid', 'label', 'publication',)
        read_only_fields = ('uuid',)
        extra_kwargs = {
            'creator': {'write_only': True}
        }

    @transaction.atomic
    def create(self, validated_data):
        try:
            request = self.context['request']
        except KeyError:
            raise NotAcceptable()

        # Append request to objects
        if request:
            setattr(Media, 'request', request)

        person = getattr(request.user, 'person', None)
        if person is None:
            raise NotAcceptable()

        if not check_validation_passed(self, request=request):
            raise PermissionDenied(detail=_("Akun belum divalidasi."))

        # Create object, default status is PENDING
        return Media.objects.create(status=PENDING, **validated_data)

    @transaction.atomic
    def update(self, instance, validated_data):
        try:
            request = self.context['request']
        except KeyError:
            raise NotAcceptable()

        # Updata object
        instance.label = validated_data.get('label', instance.label)
        instance.publication = validated_data.get(
            'publication', instance.publication)
        instance.save()

        # Update attribute
        update_attribute_values(instance, identifiers=None, values=request.data)
        return instance
