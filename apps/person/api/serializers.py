from django.db import transaction
from django.contrib.auth import get_user_model
from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import ObjectDoesNotExist

# THIRD PARTY
from rest_framework import serializers
from rest_framework.response import Response
from rest_framework import status

from utils.validators import get_model
from ..utils.auths import (get_user_with_uuid, check_verified_email,
                           check_verified_phone)

Person = get_model('person', 'Person')
Attribute = get_model('person', 'Attribute')
AttributeValue = get_model('person', 'AttributeValue')
AttributeOptionGroup = get_model('person', 'AttributeOptionGroup')
Role = get_model('person', 'Role')
UserModel = get_user_model()


class PersonSerializer(serializers.ModelSerializer):
    """
    Serialize Person, not user
    Only user as Person show
    """
    name = serializers.CharField(source='user.username', read_only=True)
    url = serializers.HyperlinkedIdentityField(
        view_name='persons:person-detail', lookup_field='uuid', read_only=True)

    class Meta:
        model = Person
        fields = ['uuid', 'name', 'url']
        read_only_fields = ['uuid']
        ordering = ['name']


class SingleSerializer(serializers.ModelSerializer):
    """
    Serialize Person, not user
    Only user as Person show
    """
    name = serializers.CharField(source='user.username', read_only=True)
    roles = serializers.StringRelatedField(many=True)
    options = serializers.StringRelatedField(many=True)
    attribute_values = serializers.SerializerMethodField()

    class Meta:
        model = Person
        fields = ['uuid', 'name', 'roles', 'options', 'attribute_values']
        read_only_fields = ['uuid']

    def get_attribute_values(self, obj):
        values_dict = {}
        request = self.context['request']
        values = obj.attribute_values \
            .prefetch_related('attribute') \
            .select_related('attribute') \
            .all()

        if values.exists():
            for value in values:
                attr_type = value.attribute.type
                identifier = value.attribute.identifier
                name = 'value_%s' % attr_type
                content = getattr(value, name)

                # Has value
                if content:
                    # Image and file has url
                    if attr_type == 'image' or attr_type == 'file':
                        url = content.url
                        content = request.build_absolute_uri(url)

                    if attr_type == 'option':
                        content = content.option

                    if attr_type == 'multi_option':
                        option = content \
                            .prefetch_related('attributevalue') \
                            .select_related('attributevalue') \
                            .defer('attributevalue') \
                            .values('option')
                        content = option
                    values_dict[identifier] = content
            return values_dict
        return None


class CreateSerializer(serializers.ModelSerializer):
    """
    Actually not create Person
    This create User then make as Person
    """
    uuid = serializers.UUIDField(source='person.uuid', read_only=True)
    verified_email = serializers.SerializerMethodField(read_only=True)
    verified_phone = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = UserModel
        fields = ['username', 'email', 'password', 'uuid',
                  'verified_email', 'verified_phone']
        extra_kwargs = {
            'password': {
                'write_only': True,
                'min_length': 6
            },
            'username': {
                'min_length': 4,
                'max_length': 15
            },
            'email': {
                'write_only': True,
                'required': True
            },
            'telephone': {
                'write_only': True,
                'required': True
            }
        }

    def get_verified_email(self, obj):
        if hasattr(obj, 'person'):
            person = obj.person
            return check_verified_email(self, person=person)
        return None

    def get_verified_phone(self, obj):
        if hasattr(obj, 'person'):
            person = obj.person
            return check_verified_phone(self, person=person)
        return None

    def validate(self, data):
        # Request data
        request_data = self.context['request'].data

        # Each user only allow one email (unique)
        email = data.get('email', self.instance.email if self.instance is not
                         None else None)
        username = data.get('username', self.instance.username if
                            self.instance is not None else None)
        telephone = str(request_data.get('telephone', None))

        if email and username:
            if UserModel.objects.filter(email=email).exclude(
                    username=username).exists():
                raise serializers.ValidationError({
                    'email': _('Email has been used.')
                })

        if telephone is None:
            raise serializers.ValidationError({
                'telephone': _('Telephone number empty.')
            })
        elif not telephone.isdigit():
            raise serializers.ValidationError({
                'telephone': _('Telephone number only.')
            })
        elif len(telephone) < 10 or len(telephone) > 14:
            raise serializers.ValidationError({
                'telephone': _('Telephone number min 10 and max 14 digits.')
            })
        return data

    @transaction.atomic
    def create(self, validated_data):
        user = UserModel.objects.create_user(**validated_data)

        try:
            request = self.context['request']
        except KeyError:
            request = None

        # Now make as Person with default role Registered
        # Make sure Role exist
        try:
            roles = Role.objects.filter(is_active=True, is_default=True)
        except Role.DoesNotExist:
            roles = None

        # Make User as Person and add Roles
        try:
            person = Person.objects.create(user_id=user.pk)
        except Person.DoesNotExist:
            person = None

        if person is not None:
            if roles is not None:
                person.roles.add(*roles)

            # Append request
            # This attribute can use in signals
            setattr(person, 'request', request)
            person.save()
        return user


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
        attr_type = obj.type
        request = self.context['request']
        person_uuid = request.GET.get('person_uuid', None)
        name = 'value_%s' % attr_type
        value = getattr(obj, name, None)
        value_print = None

        # Attributes view by other person
        if person_uuid:
            user = get_user_with_uuid(self, uuid_init=person_uuid)
        else:
            user = request.user

        person = getattr(user, 'person', None)
        if person:
            if attr_type == 'image' and hasattr(obj, 'value_image'):
                try:
                    obj_file = obj.attributevalue_set \
                        .get(person=person, attribute__identifier=obj.identifier)
                except ObjectDoesNotExist:
                    obj_file = None

                # Make sure not empty
                if obj_file and obj_file.value_image:
                    value = request.build_absolute_uri(
                        obj_file.value_image.url)

            if attr_type == 'file' and hasattr(obj, 'value_file'):
                try:
                    obj_file = obj.attributevalue_set \
                        .get(person=person, attribute__identifier=obj.identifier)
                except ObjectDoesNotExist:
                    obj_file = None

                # Make sure not empty
                if obj_file and obj_file.value_file:
                    value = request.build_absolute_uri(
                        obj_file.value_file.url)

            if attr_type == 'multi_option':
                value = []
                value_print = []
                option = obj.attributevalue_set \
                    .prefetch_related('person', 'attribute',
                                      'value_multi_option') \
                    .select_related('person', 'attribute',
                                    'value_multi_option') \
                    .filter(
                        person=person,
                        attribute__identifier=obj.identifier
                    ) \
                    .defer('person', 'attribute', 'value_multi_option') \
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

            value_dict = {
                'field': name,
                'object': value,
                'object_print': value_print
            }
            return value_dict
        return None
