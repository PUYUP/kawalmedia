from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.db import IntegrityError
from django.db.models import Q

# LOCAL UTILS
from .utils.attributes import (
    set_attributes,
    update_attribute_values
)

# PROJECT UTILS
from utils.validators import get_model

UserModel = get_user_model()
AttributeValue = get_model('person', 'AttributeValue')
Validation = get_model('person', 'Validation')
ValidationValue = get_model('person', 'ValidationValue')


# Create signals
def user_handler(sender, instance, created, **kwargs):
    if not created:
        person = getattr(instance, 'person', None)

        if person:
            content_type = ContentType.objects.get_for_model(person)
            validation_type = Validation.objects.get(identifier='email')

            validation_value, created = ValidationValue.objects \
                .update_or_create(
                    validation=validation_type,
                    object_id=person.pk,
                    content_type=content_type)
            validation_value.value_email = instance.email
            validation_value.save()


def person_handler(sender, instance, created, **kwargs):
    user = getattr(instance, 'user', None)
    is_register = getattr(instance, 'is_register', None)

    if is_register and user:
        content_type = ContentType.objects.get_for_model(instance)
        validation_type = Validation.objects.get(identifier='email')

        validation_value, created = ValidationValue.objects \
            .update_or_create(
                validation=validation_type,
                object_id=instance.pk,
                content_type=content_type,
                verified=False)
        validation_value.value_email = user.email
        validation_value.save()

    # Attribute created after save because roles exists after add action
    if created is not True:
        # Set attributes by user Roles
        set_attributes(instance)

        # Capture data from form action
        if hasattr(instance, 'request'):
            request = instance.request
            data = request.data if hasattr(request, 'data') else None
            keys, values = list(), dict()

            if data is not None:
                for key in data:
                    keys.append(key)
                    values[key] = data[key]
                update_attribute_values(
                    instance, identifiers=keys, values=values)


def attribute_handler(sender, instance, created, **kwargs):
    if created:
        """Assign this Attribute to all user
        Based on their roles"""
        roles = instance.roles.all()
        identifier = instance.identifier
        if roles.exists():
            users = UserModel.objects.filter(
                Q(person__isnull=False),
                Q(person__roles__in=roles),
                ~Q(person__attribute_values__attribute__identifier=identifier)
            ).distinct()

            attributes_list = list()
            if users.exists():
                model_field = 'value_%s' % instance.field_type
                for user in users:
                    person = getattr(user, 'person', None)
                    if person:
                        attr_obj = AttributeValue(
                            attribute=instance,
                            content_object=person)

                        # Value for option must set from their ForeignKey
                        if instance.field_type == 'option':
                            pass
                        elif instance.field_type == 'multi_option':
                            pass
                        else:
                            setattr(attr_obj, model_field, None)
                        attributes_list.append(attr_obj)

                try:
                    AttributeValue.objects.bulk_create(attributes_list)
                except IntegrityError:
                    pass


def person_roles_handler(sender, **kwargs):
    instance = kwargs['instance']
    set_attributes(instance)
