from uuid import UUID

from django.db import transaction
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.contenttypes.models import ContentType

# THIRD PARTY
from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.exceptions import NotFound, NotAcceptable

# PROJECT UTILS
from utils.validators import get_model

# LOCAL MODELS
from ...models.models import __all__ as model_index

Attribute = get_model('escort', 'Attribute')
AttributeValue = get_model('escort', 'AttributeValue')
AttributeOptionGroup = get_model('escort', 'AttributeOptionGroup')


class OptionGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = AttributeOptionGroup
        fields = '__all__'


class AttributeValueSerializer(serializers.ModelSerializer):
    class Meta:
        model = AttributeValue
        exclude = ('id', 'object_id', 'content_type', 'attribute',)

    @transaction.atomic
    def update(self, instance, validated_data):
        try:
            request = self.context['request']
        except KeyError:
            raise NotAcceptable()

        value = request.data.get('value', None)
        if value:
            field_type = instance.attribute.field_type
            field_value = 'value_%s' % field_type
            setattr(instance, field_value, value)
            instance.save()
        return instance


class CreateAttributeValueSerializer(serializers.ModelSerializer):
    """
    {
        "entity_index": 0,
        "entity_uuid": "331ac501-805b-4243-95ae-c7ce87d8ae64",
        'attribute_uuid": "5c4157fb-42e8-43ef-bd80-12a3d013a066",
        "value": "My value"
    }
    """

    class Meta:
        model = AttributeValue
        exclude = ('id',)
        read_only_fields = ('uuid',)
        extra_kwargs = {
            'content_type': {'write_only': True},
            'object_id': {'write_only': True},
            'content_object': {'write_only': True}
        }

    def __init__(self, **kwargs):
        data = kwargs['data']

        # Validate parameter required here
        try:
            entity_index = data['entity_index']
        except KeyError:
            raise NotFound()

        try:
            entity_uuid = data['entity_uuid']
            try:
                entity_uuid = UUID(entity_uuid)
            except ValueError:
                raise NotFound()
        except KeyError:
            raise NotFound()

        try:
            attribute_uuid = data['attribute_uuid']

            if type(attribute_uuid) is not UUID:
                try:
                    attribute_uuid = UUID(attribute_uuid)
                except ValueError:
                    raise NotFound()
        except KeyError:
            raise NotFound()

        try:
            attribute_object = Attribute.objects \
                .get(uuid=attribute_uuid)
            kwargs['data']['attribute'] = attribute_object.pk
        except ObjectDoesNotExist:
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

        model_name = entity_model._meta.model_name  # ex: media, comment

        try:
            entity_type = ContentType.objects.get(
                app_label='escort', model=model_name)
        except ObjectDoesNotExist:
            raise NotFound()

        try:
            entity_object = entity_model.objects.get(uuid=entity_uuid)
            kwargs['data']['object_id'] = entity_object.pk
            kwargs['data']['content_type'] = entity_type.pk
        except ObjectDoesNotExist:
            raise NotFound()

        super().__init__(**kwargs)

    @transaction.atomic
    def create(self, validated_data):
        try:
            request = self.context['request']
        except KeyError:
            raise NotAcceptable()

        # Append request to objects
        if request:
            setattr(AttributeValue, 'request', request)

        # Prepare value
        value = request.data.get('value', None)
        if not value:
            raise NotFound()

        attribute = validated_data.get('attribute', None)
        field_type = attribute.field_type

        # Append value
        validated_data.update({'value_%s' % field_type: value})
        return AttributeValue.objects.create(**validated_data)


class AttributeSerializer(serializers.ModelSerializer):
    """ Serialize Attribute"""
    url = serializers.HyperlinkedIdentityField(
        view_name='escorts:attribute-detail', lookup_field='uuid', read_only=True)
    option_group = serializers.SerializerMethodField()
    value = serializers.SerializerMethodField()

    class Meta:
        model = Attribute
        exclude = ('id', 'content_type',)

    def get_option_group(self, obj):
        # option_group
        if obj.option_group:
            options = obj.option_group.options.all().values('id', 'option')
            return options
        return None

    def get_value(self, obj):
        """Show value if entity_uuid defined"""
        attr_type = obj.field_type
        request = self.context['request']
        entity_uuid = request.GET.get('entity_uuid', None)
        entity_index = request.GET.get('entity_index', None)
        name = 'value_%s' % attr_type
        value = getattr(obj, name, None)
        value_print = None

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

        model_name = entity_model._meta.model_name  # ex: media, comment

        if entity_uuid:
            if attr_type == 'image' and hasattr(obj, 'value_image'):
                obj_file = obj.attributevalue_set \
                    .get(
                        **{'%s__uuid' % model_name: entity_uuid},
                        attribute__identifier=obj.identifier)

                # Make sure not empty
                if obj_file.value_image:
                    value = request.build_absolute_uri(
                        obj_file.value_image.url)

            if attr_type == 'file' and hasattr(obj, 'value_file'):
                obj_file = obj.attributevalue_set \
                    .get(
                        **{'%s__uuid' % model_name: entity_uuid},
                        attribute__identifier=obj.identifier)

                # Make sure not empty
                if obj_file.value_file:
                    value = request.build_absolute_uri(
                        obj_file.value_file.url)

            if attr_type == 'multi_option':
                value = list()
                value_print = list()
                option = obj.attributevalue_set \
                    .prefetch_related(
                        model_name, 'attribute', 'value_multi_option') \
                    .select_related(
                        model_name, 'attribute', 'value_multi_option') \
                    .filter(
                        **{'%s__uuid' % model_name: entity_uuid},
                        attribute__identifier=obj.identifier
                    ) \
                    .defer(model_name, 'attribute', 'value_multi_option') \
                    .values(
                        'value_multi_option__id',
                        'value_multi_option__option'
                    )

                if option:
                    for opt in option:
                        id = opt.get('value_multi_option__id', None)
                        label = opt.get('value_multi_option__option', None)
                        value.append(id)
                        value_print.append(label)
        # Output
        value_dict = {
            'uuid': getattr(obj, 'value_uuid', None),
            'field': name,
            'object': value,
            'object_print': value_print,
            'required': obj.required,
        }
        return value_dict
