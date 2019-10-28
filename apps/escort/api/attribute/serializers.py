import uuid

# THIRD PARTY
from rest_framework import serializers
from rest_framework.response import Response

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
        fields = '__all__'


class AttributeSerializer(serializers.ModelSerializer):
    """ Serialize Attribute"""
    option_group = serializers.SerializerMethodField()
    value = serializers.SerializerMethodField()

    class Meta:
        model = Attribute
        fields = '__all__'

    def get_option_group(self, obj):
        # option_group
        if obj.option_group:
            options = obj.option_group.options.all().values('id', 'option')
            return options
        return None

    def get_value(self, obj):
        """Show value if entity_uuid defined"""
        attr_type = obj.type
        request = self.context['request']
        entity_uuid = request.GET.get('entity_uuid', None)
        entity_index = request.GET.get('entity_index', None)
        name = 'value_%s' % attr_type
        value_print = None
        value = None

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
            value = getattr(obj, name, None)

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
                value = []
                value_print = []
                option = obj.attributevalue_set \
                    .prefetch_related(model_name, 'attribute',
                                      'value_multi_option') \
                    .select_related(model_name, 'attribute',
                                    'value_multi_option') \
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
            'field': name,
            'object': value,
            'object_print': value_print,
            'required': obj.required,
        }
        return value_dict
