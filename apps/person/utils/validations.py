import asyncio
import uuid

from django.conf import settings
from django.db import IntegrityError
from django.db.models import Q
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.contenttypes.models import ContentType

from utils.validators import get_model

Validation = get_model('person', 'Validation')
ValidationValue = get_model('person', 'ValidationValue')

loop = asyncio.get_event_loop()


def upload_image(args):
    """ Upload as image """
    instance = args['instance']
    value = args['value']
    filename = value

    if type(value) is list and value:
        file = value[0]
        filename = file.name
        value = file
        instance.value_image.save(filename, value, save=True)

    if value is None:
        instance.value_image.delete()


def upload_file(args):
    """ Upload as general file """
    instance = args['instance']
    value = args['value']
    filename = value

    if type(value) is list and value:
        file = value[0]
        filename = file.name
        value = file
        instance.value_file.save(filename, value, save=True)

    if value is None:
        instance.value_image.delete()


def set_validations(entity, *agrs, **kwargs):
    """
    Create default validations value
    Currated by entity
    """
    # Check database model Validation
    if Validation and ValidationValue and entity:
        roles = None
        validations = None
        validation_params = dict()

        # Check user has roles
        if entity and hasattr(entity, 'roles'):
            roles = entity.roles.all()

        # Extract entity
        entity_type = ContentType.objects.get_for_model(entity)

        # Set validation params
        # validation_params.update({'content_type': entity_type})

        # Add role to filter
        if roles:
            validation_params.update({'roles__in': roles})

        # Grab all validation not for this entity
        # But keep its unique!
        validations = Validation.objects \
            .filter(content_type=entity_type) \
            .distinct()

        # Prepare delete old validations
        old_validations = validations.exclude(**validation_params)
        if old_validations.exists():
            # return None
            old_validations_obj = entity.validation_values \
                .filter(validation__in=old_validations)

            # Run delete if exists
            if old_validations_obj:
                old_validations_obj.delete()

        # Get all validations by entity type (ex: Media, Person, ect...)
        # If entity validation ready, create the default values
        validations = validations.filter(**validation_params)
        if validations.exists():
            values_list = list()
            for attr in validations:
                # Make sure not append if value is ready
                try:
                    # Make sure set validation based on target object
                    value_obj = entity.validation_values.get(
                        validation__field_type=attr.field_type,
                        validation__identifier=attr.identifier)
                except ObjectDoesNotExist:
                    value_obj = None

                # If value not ready, append it
                if not value_obj:
                    model_field = 'value_%s' % attr.field_type
                    attr_obj = ValidationValue(
                        validation=attr,
                        content_object=entity)

                    setattr(attr_obj, model_field, None)
                    values_list.append(attr_obj)

            # Create default validation for models
            if values_list:
                try:
                    return ValidationValue.objects \
                        .bulk_create(values_list)
                except IntegrityError:
                    pass
            return None
        return None
    return None


def assign_validations(entity, *agrs, **kwargs):
    validation_objects = kwargs.get('validation_objects', None)
    validation_keys = kwargs.get('validation_keys', None)
    validation_keys_define = kwargs.get('validation_keys_define', None)
    validation_values_list = list()

    if validation_objects and validation_keys and validation_keys_define:
        for attr in validation_objects:
            model_field = 'value_%s' % attr.field_type
            attr_value_obj = ValidationValue(
                validation=attr,
                content_object=entity)

            setattr(attr_value_obj, model_field, None)
            validation_values_list.append(attr_value_obj)

        # Create default validation for entity
        if validation_values_list:
            try:
                # Create validation value
                ValidationValue.objects.bulk_create(validation_values_list)

                # After created, get validations value from entity
                return entity.validation_values \
                    .filter(validation__identifier__in=validation_keys_define)
            except IntegrityError:
                return None
    return None


def update_validation_values(entity, *agrs, **kwargs):
    """
    Update validations value
    Currated by entity
    ------------------------
    kwargs = {
        'identifier': 'value',
        ...
    }
    """
    identifiers = kwargs.get('identifiers', None)
    values = kwargs.get('values', None)

    # Check database model Validation
    if Validation and ValidationValue and values:
        attr_values_obj, attr_values_type, validation_keys = list(), list(), list()

        try:
            values = dict(values.lists())
        except AttributeError:
            values = values

        if values and type(values) is dict:
            for value in values:
                validation_keys.append(value)
        else:
            return None

        # Update single validation by identifiers
        if identifiers:
            validation_keys = identifiers

        # Get original identifiers
        validation_keys_define = validation_keys

        # All validations
        validation_values = entity.validation_values \
            .filter(validation__identifier__in=validation_keys)

        # Hapus validation_keys jika sudah ada dalam validation_values
        if validation_values.exists():
            for value in validation_values:
                validation = value.validation
                identifier = getattr(validation, 'identifier', None)
                if identifier:
                    validation_keys.remove(identifier)

        # ContentType berdasarkan entity (model)
        entity_type = ContentType.objects.get_for_model(entity)

        # Extrak validation yang belum ter-assign
        validation_unassign = Validation.objects \
            .filter(
                content_type=entity_type,
                identifier__in=validation_keys) \
            .distinct()

        # Assign-kan validation ini
        # Kemudian replace validation_values dengan yang baru
        if validation_unassign.exists():
            validation_values = assign_validations(
                entity,
                validation_keys=validation_keys,
                validation_keys_define=validation_keys_define,
                validation_objects=validation_unassign)

        # Escort has validations
        if validation_values and validation_values.exists():
            for attr in validation_values:
                attr_type = attr.validation.field_type
                model_field = 'value_%s' % attr_type
                identifier = attr.validation.identifier
                attr_obj = validation_values.get(
                    validation__identifier=identifier)

                # Grab value
                try:
                    value = values[identifier]
                except KeyError:
                    value = None

                # Set arguments
                if attr_type == 'file' or attr_type == 'image':
                    arguments = {'instance': attr_obj, 'value': value}

                if attr_type == 'file':
                    # Upload file
                    loop.run_in_executor(None, upload_file, arguments)
                elif attr_type == 'image':
                    # Upload image
                    loop.run_in_executor(None, upload_image, arguments)
                else:
                    # Set the value
                    setattr(attr_obj, model_field, value)

                    # Append all value types
                    attr_values_type.append(model_field)
                attr_values_obj.append(attr_obj)

            # Bulk update validations value
            if attr_values_obj and attr_values_type:
                return ValidationValue.objects.bulk_update(
                    attr_values_obj, attr_values_type)
            return None
        return None
    return None
