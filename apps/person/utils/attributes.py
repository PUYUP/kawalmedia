import asyncio
import uuid

from django.conf import settings
from django.db import IntegrityError
from django.db.models import Q
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.contenttypes.models import ContentType

from utils.validators import get_model

Attribute = get_model('person', 'Attribute')
AttributeValue = get_model('person', 'AttributeValue')

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


def set_attributes(entity, *agrs, **kwargs):
    """
    Create default attributes value
    Currated by entity
    """
    # Check database model Attribute
    if Attribute and AttributeValue and entity:
        roles = None
        attributes = None
        attribute_params = {}

        # Check user has roles
        if entity and hasattr(entity, 'roles'):
            roles = entity.roles.all()

        # Extract entity
        entity_type = ContentType.objects.get_for_model(entity)

        # Set attribute params
        # attribute_params.update({'content_type': entity_type})

        # Add role to filter
        if roles:
            attribute_params.update({'roles__in': roles})

        # Grab all attribute not for this entity
        # But keep its unique!
        attributes = Attribute.objects \
            .filter(content_type=entity_type) \
            .distinct()

        # Prepare delete old attributes
        old_attributes = attributes.exclude(**attribute_params)
        if old_attributes.exists():
            # return None
            old_attributes_obj = entity.attribute_values \
                .filter(attribute__in=old_attributes)

            # Run delete if exists
            if old_attributes_obj:
                old_attributes_obj.delete()

        # Get all attributes by entity type (ex: Media, Person, ect...)
        # If entity attribute ready, create the default values
        attributes = attributes.filter(**attribute_params)
        if attributes.exists():
            values_list = []
            for attr in attributes:
                # Make sure not append if value is ready
                try:
                    # Make sure set attribute based on target object
                    value_obj = entity.attribute_values.get(
                        attribute__type=attr.type,
                        attribute__identifier=attr.identifier)
                except ObjectDoesNotExist:
                    value_obj = None

                # If value not ready, append it
                if not value_obj:
                    model_field = 'value_%s' % attr.type
                    attr_obj = AttributeValue(
                        attribute=attr,
                        content_object=entity)

                    # Value for option and multi must set from their ForeignKey
                    if attr.type == 'option':
                        pass
                    elif attr.type == 'multi_option':
                        pass
                    else:
                        setattr(attr_obj, model_field, None)
                    values_list.append(attr_obj)

            # Create default attribute for models
            if values_list:
                try:
                    return AttributeValue.objects \
                        .bulk_create(values_list)
                except IntegrityError:
                    pass
            return None
        return None
    return None


def assign_attributes(entity, *agrs, **kwargs):
    attribute_objects = kwargs.get('attribute_objects', None)
    attribute_keys = kwargs.get('attribute_keys', None)
    attribute_keys_define = kwargs.get('attribute_keys_define', None)
    attribute_values_list = []

    if attribute_objects and attribute_keys and attribute_keys_define:
        for attr in attribute_objects:
            model_field = 'value_%s' % attr.type
            attr_value_obj = AttributeValue(
                attribute=attr,
                content_object=entity)

            # Value for option and multi must set from their ForeignKey
            if attr.type == 'option':
                pass
            elif attr.type == 'multi_option':
                pass
            else:
                setattr(attr_value_obj, model_field, None)
            attribute_values_list.append(attr_value_obj)

        # Create default attribute for entity
        if attribute_values_list:
            try:
                # Create attribute value
                AttributeValue.objects.bulk_create(attribute_values_list)

                # After created, get attributes value from entity
                return entity.attribute_values \
                    .filter(attribute__identifier__in=attribute_keys_define)
            except IntegrityError:
                return None
    return None


def update_attribute_values(entity, *agrs, **kwargs):
    """
    Update attributes value
    Currated by entity
    ------------------------
    kwargs = {
        'identifier': 'value',
        ...
    }
    """
    identifiers = kwargs.get('identifiers', None)
    values = kwargs.get('values', None)

    # Check database model Attribute
    if Attribute and AttributeValue and values:
        attr_values_obj, attr_values_type, attribute_keys = [], [], []

        try:
            values = dict(values.lists())
        except AttributeError:
            values = values

        if values and type(values) is dict:
            for value in values:
                attribute_keys.append(value)
        else:
            return None

        # Update single attribute by identifiers
        if identifiers:
            attribute_keys = identifiers

        # Get original identifiers
        attribute_keys_define = attribute_keys

        # All attributes
        attribute_values = entity.attribute_values \
            .filter(attribute__identifier__in=attribute_keys)

        # Hapus attibute_keys jika sudah ada dalam attribute_values
        if attribute_values.exists():
            for value in attribute_values:
                attribute = value.attribute
                identifier = getattr(attribute, 'identifier', None)
                if identifier:
                    attribute_keys.remove(identifier)

        # ContentType berdasarkan entity (model)
        entity_type = ContentType.objects.get_for_model(entity)

        # Extrak attribute yang belum ter-assign
        attribute_unassign = Attribute.objects \
            .filter(
                content_type=entity_type,
                identifier__in=attribute_keys) \
            .distinct()

        # Assign-kan attribute ini
        # Kemudian replace attribute_values dengan yang baru
        if attribute_unassign.exists():
            attribute_values = assign_attributes(
                entity,
                attribute_keys=attribute_keys,
                attribute_keys_define=attribute_keys_define,
                attribute_objects=attribute_unassign)

        # Escort has attributes
        if attribute_values and attribute_values.exists():
            for attr in attribute_values:
                attr_type = attr.attribute.type
                model_field = 'value_%s' % attr_type
                identifier = attr.attribute.identifier
                attr_obj = attribute_values.get(
                    attribute__identifier=identifier)

                # Grab value
                try:
                    value = values[identifier]
                except KeyError:
                    value = None

                # Set arguments
                if attr_type == 'file' or attr_type == 'image':
                    arguments = {'instance': attr_obj, 'value': value}

                # Value for option and multi must set from their ForeignKey
                if attr_type == 'option':
                    # Get options object
                    try:
                        value = attr_obj.attribute \
                            .option_group.options.get(id=value)
                    except ObjectDoesNotExist:
                        value = None

                    setattr(attr_obj, model_field, value)
                    attr_obj.save()
                elif attr_type == 'multi_option':
                    # Multi option
                    getattr(attr_obj, model_field).set(filter(None, value))
                elif attr_type == 'file':
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

            # Bulk update attributes value
            if attr_values_obj and attr_values_type:
                return AttributeValue.objects.bulk_update(
                    attr_values_obj, attr_values_type)
            return None
        return None
    return None
