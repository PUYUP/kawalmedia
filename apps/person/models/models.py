from django.db import models

from .models_abstract import *
from .models_attribute import *
from utils.validators import is_model_registered

__all__ = []

if not is_model_registered('person', 'Role'):
    class Role(AbstractRole):
        class Meta(AbstractRole.Meta):
            db_table = 'person_role'

    __all__.append('Role')


if not is_model_registered('person', 'Person'):
    class Person(AbstractPerson):
        class Meta(AbstractPerson.Meta):
            db_table = 'person'

    __all__.append('Person')


# Attribute

if not is_model_registered('person', 'Attribute'):
    class Attribute(AbstractAttribute):
        class Meta(AbstractAttribute.Meta):
            db_table = 'person_attribute'

    __all__.append('Attribute')


if not is_model_registered('person', 'AttributeValue'):
    class AttributeValue(AbstractAttributeValue):
        class Meta(AbstractAttributeValue.Meta):
            db_table = 'person_attribute_value'

    __all__.append('AttributeValue')


if not is_model_registered('person', 'AttributeOption'):
    class AttributeOption(AbstractAttributeOption):
        class Meta(AbstractAttributeOption.Meta):
            db_table = 'person_attribute_option'

    __all__.append('AttributeOption')


if not is_model_registered('person', 'AttributeOptionGroup'):
    class AttributeOptionGroup(AbstractAttributeOptionGroup):
        class Meta(AbstractAttributeOptionGroup.Meta):
            db_table = 'person_attribute_option_group'

    __all__.append('AttributeOptionGroup')


if not is_model_registered('person', 'Option'):
    class Option(AbstractOption):
        class Meta(AbstractOption.Meta):
            db_table = 'person_option'

    __all__.append('Option')
