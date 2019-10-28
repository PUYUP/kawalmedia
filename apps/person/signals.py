from django.dispatch import receiver
from django.contrib.auth import get_user_model
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


# Create signals
def person_handler(sender, instance, created, **kwargs):
    # Attribute created after save because roles exists after add action
    if created is not True:
        # Set attributes by user Roles
        set_attributes(instance)

        # Capture data from form action
        if hasattr(instance, 'request'):
            request = instance.request
            data = request.data if hasattr(request, 'data') else None
            keys, values = [], {}

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

            attributes_list = []
            if users.exists():
                model_field = 'value_%s' % instance.type
                for user in users:
                    person = getattr(user, 'person', None)
                    if person:
                        attr_obj = AttributeValue(
                            attribute=instance,
                            content_object=person)

                        # Value for option must set from their ForeignKey
                        if instance.type == 'option':
                            pass
                        elif instance.type == 'multi_option':
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
