from django.db import transaction
from django.contrib.auth import get_user_model
from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import ObjectDoesNotExist

# THIRD PARTY
from rest_framework import serializers
from rest_framework.response import Response
from rest_framework import status

from utils.validators import get_model

Attribute = get_model('person', 'Attribute')
AttributeValue = get_model('person', 'AttributeValue')
AttributeOptionGroup = get_model('person', 'AttributeOptionGroup')


class OptionGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = AttributeOptionGroup
        fields = '__all__'


class AttributeValueSerializer(serializers.ModelSerializer):
    class Meta:
        model = AttributeValue
        fields = '__all__'


class AttributeSerializer(serializers.ModelSerializer):
    """ Serialize Attribute, not user
    Only user as Person show """
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
        attr_type = obj.field_type
        request = self.context['request']
        person = getattr(request.user, 'person', None)
        name = 'value_%s' % attr_type
        value = getattr(obj, name, None)
        value_print = None

        if person:
            if attr_type == 'image' and hasattr(obj, 'value_image'):
                try:
                    obj_file = obj.attributevalue_set.get(
                        person=person, attribute__identifier=obj.identifier)
                except ObjectDoesNotExist:
                    obj_file = None

                # Make sure not empty
                if obj_file and obj_file.value_image:
                    value = request.build_absolute_uri(
                        obj_file.value_image.url)

            if attr_type == 'file' and hasattr(obj, 'value_file'):
                try:
                    obj_file = obj.attributevalue_set.get(
                        person=person, attribute__identifier=obj.identifier)
                except ObjectDoesNotExist:
                    obj_file = None

                # Make sure not empty
                if obj_file and obj_file.value_file:
                    value = request.build_absolute_uri(
                        obj_file.value_file.url)

            if attr_type == 'multi_option':
                value = list()
                value_print = list()
                option = obj.attributevalue_set \
                    .prefetch_related('person', 'attribute',
                                      'value_multi_option', 'content_object') \
                    .select_related('person', 'attribute',
                                    'value_multi_option', 'content_object') \
                    .filter(
                        person=person,
                        attribute__identifier=obj.identifier) \
                    .defer('person', 'attribute', 'value_multi_option',
                           'content_object') \
                    .values(
                        'value_multi_option__id',
                        'value_multi_option__option')

                if option:
                    for opt in option:
                        id = opt.get('value_multi_option__id', None)
                        label = opt.get('value_multi_option__option', None)
                        value.append(id)
                        value_print.append(label)

            value_dict = {
                'uuid': getattr(obj, 'value_uuid', None),
                'field': name,
                'object': value,
                'object_print': value_print
            }
            return value_dict
        return None
