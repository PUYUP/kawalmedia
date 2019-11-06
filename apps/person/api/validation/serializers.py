from uuid import UUID

from django.db import transaction
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth import get_user_model
from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import ObjectDoesNotExist

# THIRD PARTY
from rest_framework import serializers
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import NotAcceptable

# PROJECT UTILS
from utils.validators import get_model

# LOCAL UTILS
from ...utils.auths import validate_secure_code

Validation = get_model('person', 'Validation')
ValidationValue = get_model('person', 'ValidationValue')


class ValidationValueSerializer(serializers.ModelSerializer):
    """
    {
        "value": "12345",
        "value_uuid": "e01cb827-ae90-4944-a059-65192724f71b",
        "secure_code": "3435"
    }
    """
    class Meta:
        model = ValidationValue
        exclude = ('id', 'object_id', 'content_type', 'validation',)

    @transaction.atomic
    def update(self, instance, validated_data):
        try:
            request = self.context['request']
        except KeyError:
            raise NotAcceptable()

        # Append request
        setattr(self, 'request', request)

        method = instance.validation.method
        identifier = instance.validation.identifier
        field_type = instance.validation.field_type
        field_value = 'value_%s' % field_type
        secure_code = request.data.get('secure_code', None)
        value = request.data.get('value', None)

        # Need validate critical action
        if secure_code:
            if method == 1:
                if not validate_secure_code(self, secure_code=secure_code):
                    raise NotAcceptable(detail=_("Kode otentikasi salah."))

            if method == 0:
                instance_secure_code = instance.secure_code
                if secure_code != instance_secure_code:
                    raise NotAcceptable(detail=_("Kode otentikasi salah."))

            # Make veridied!
            instance.verified = True
        else:
            # Change value, so un-verified
            instance.verified = False

        if value:
            # Update user email to
            if identifier == 'email':
                user = getattr(request, 'user', None)
                if user:
                    user.email = value
                    user.save()

            setattr(instance, field_value, value)
            instance.save()
        return instance


class CreateValidationValueSerializer(serializers.ModelSerializer):
    """
    {
        "entity_index": 0,
        "entity_uuid": "331ac501-805b-4243-95ae-c7ce87d8ae64",
        'validation_uuid": "5c4157fb-42e8-43ef-bd80-12a3d013a066",
        "value": "My value"
    }
    """

    class Meta:
        model = ValidationValue
        exclude = ('id',)
        read_only_fields = ('uuid',)
        extra_kwargs = {
            'content_type': {'write_only': True},
            'object_id': {'write_only': True},
            'content_object': {'write_only': True}
        }

    def __init__(self, **kwargs):
        data = kwargs['data']
        context = kwargs['context']

        try:
            request = context['request']
        except KeyError:
            raise NotAcceptable()

        person = getattr(request.user, 'person', None)
        if not person:
            raise NotAcceptable()

        try:
            validation_uuid = data['validation_uuid']

            if type(validation_uuid) is not UUID:
                try:
                    validation_uuid = UUID(validation_uuid)
                except ValueError:
                    raise NotFound()
        except KeyError:
            raise NotFound()

        try:
            validation_object = Validation.objects \
                .get(uuid=validation_uuid)
            kwargs['data']['validation'] = validation_object.pk
        except ObjectDoesNotExist:
            raise NotFound()

        content_type = ContentType.objects.get_for_model(person)

        try:
            kwargs['data']['object_id'] = person.pk
            kwargs['data']['content_type'] = content_type.pk
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
            setattr(ValidationValue, 'request', request)

        # Prepare value
        value = request.data.get('value', None)
        if not value:
            raise NotFound()

        validation = validated_data.get('validation', None)
        field_type = validation.field_type

        # Append value
        validated_data.update({'value_%s' % field_type: value})
        return ValidationValue.objects.create(**validated_data)


class ValidationSerializer(serializers.ModelSerializer):
    """ Serialize Validation, not user
    Only user as Person show """
    value = serializers.SerializerMethodField()
    url = serializers.HyperlinkedIdentityField(
        view_name='persons:validation-detail', lookup_field='uuid', read_only=True)

    class Meta:
        model = Validation
        exclude = ('id', 'roles', 'content_type', 'field_type',)

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
                    obj_file = obj.validationvalue_set.get(
                        person=person, validation__identifier=obj.identifier)
                except ObjectDoesNotExist:
                    obj_file = None

                # Make sure not empty
                if obj_file and obj_file.value_image:
                    value = request.build_absolute_uri(
                        obj_file.value_image.url)

            if attr_type == 'file' and hasattr(obj, 'value_file'):
                try:
                    obj_file = obj.validationvalue_set.get(
                        person=person, validation__identifier=obj.identifier)
                except ObjectDoesNotExist:
                    obj_file = None

                # Make sure not empty
                if obj_file and obj_file.value_file:
                    value = request.build_absolute_uri(
                        obj_file.value_file.url)

            value_dict = {
                'uuid': getattr(obj, 'value_uuid', None),
                'field': name,
                'object': value,
                'object_print': value_print,
                'verified': getattr(obj, 'verified', None),
            }
            return value_dict
        return None
