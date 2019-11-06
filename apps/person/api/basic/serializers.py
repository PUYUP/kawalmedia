from django.db import transaction
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import ObjectDoesNotExist
from django.core.validators import EmailValidator

# THIRD PARTY
from rest_framework import serializers
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import NotAcceptable

# PROJECT UTILS
from utils.validators import get_model

# LOCAL UTILS
from ...utils.auths import validate_secure_code

Person = get_model('person', 'Person')
Role = get_model('person', 'Role')
Validation = get_model('person', 'Validation')
ValidationValue = get_model('person', 'ValidationValue')
UserModel = get_user_model()


class DynamicFieldsModelSerializer(serializers.ModelSerializer):
    """
    A ModelSerializer that takes an additional `fields` argument that
    controls which fields should be displayed.
    """

    def __init__(self, *args, **kwargs):
        # Instantiate the superclass normally
        super().__init__(*args, **kwargs)

        fields = self.context['request'].query_params.get('fields')
        if fields:
            fields = fields.split(',')

            # Drop any fields that are not specified in the `fields` argument.
            allowed = set(fields)
            existing = set(self.fields.keys())
            for field_name in existing - allowed:
                self.fields.pop(field_name)


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
        fields = ('uuid', 'name', 'url',)
        read_only_fields = ('uuid',)
        ordering = ('name',)


class SinglePersonSerializer(DynamicFieldsModelSerializer, serializers.ModelSerializer):
    """
    Serialize Person, not user
    Only user as Person show
    """
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.CharField(source='user.email', read_only=True)
    first_name = serializers.CharField(source='user.first_name', read_only=True)
    last_name = serializers.CharField(source='user.last_name', read_only=True)
    roles = serializers.StringRelatedField(many=True)
    options = serializers.StringRelatedField(many=True)

    class Meta:
        model = Person
        exclude = ('id', 'user',)
        read_only_fields = ('uuid',)


class CreatePersonSerializer(serializers.ModelSerializer):
    """
    Actually not create Person
    This create User then make as Person
    """
    uuid = serializers.UUIDField(source='person.uuid', read_only=True)

    class Meta:
        model = UserModel
        fields = ('uuid', 'username', 'email', 'password',)
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
                'required': True,
                'validators': [EmailValidator()]
            }
        }

    def validate(self, data):
        # Request data
        request_data = self.context['request'].data

        # Each user only allow one email (unique)
        email = data.get('email', self.instance.email if self.instance is not
                         None else None)
        username = data.get('username', self.instance.username if
                            self.instance is not None else None)

        if email and username:
            if UserModel.objects.filter(email=email).exclude(
                    username=username).exists():
                raise serializers.ValidationError({
                    'email': _('Email sudah digunakan.')
                })

        return data

    def validate_password(self, value):
        validate_password(value)
        return value

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
        except ObjectDoesNotExist:
            roles = None

        # Make User as Person and add Roles
        try:
            person = Person.objects.create(user_id=user.pk)
        except ObjectDoesNotExist:
            person = None

        if person:
            if roles:
                person.roles.add(*roles)

            # Append request
            # This attribute can use in signals
            setattr(person, 'request', request)

            # Append indicator action from register
            setattr(person, 'is_register', True)

            person.save()
        return user


class UpdatePersonSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserModel
        fields = ('username', 'email', 'password', 'first_name',
                  'last_name',)
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
                'validators': [EmailValidator()]
            }
        }

    def validate_password(self, value):
        validate_password(value, user=self.instance)
        return value

    @transaction.atomic
    def update(self, instance, validated_data):
        try:
            request = self.context['request']
        except KeyError:
            raise NotAcceptable()

        # Append request
        setattr(self, 'request', request)

        # Need validate critical action
        secure_code = request.data.get('secure_code', None)
        if ('password' in validated_data or 'email' in validated_data
                or 'username' in validated_data):
            if not validate_secure_code(self, secure_code=secure_code):
                raise NotAcceptable(detail=_("Kode otentikasi salah."))

        # Updata object
        if validated_data:
            for k, v in validated_data.items():
                if 'password' in k:
                    instance.set_password(v)
                else:
                    setattr(instance, k, v)

            instance.save()

            # Don't forget update validation email to
            email = validated_data.get('email', None)
            if email:
                content_type = ContentType.objects.get_for_model(instance)
                validation_type = Validation.objects.get(identifier='email')

                validation_value, created = ValidationValue.objects \
                    .update_or_create(
                        validation=validation_type,
                        object_id=instance.pk,
                        content_type=content_type,
                        verified=True)
                validation_value.value_email = email
                validation_value.save()
        else:
            raise NotAcceptable()

        return instance
