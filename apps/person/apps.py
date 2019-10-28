from django.apps import AppConfig
from django.db.models.signals import post_save, m2m_changed


class PersonConfig(AppConfig):
    name = 'apps.person'

    def ready(self):
        from apps.person.signals import person_handler, attribute_handler, person_roles_handler
        from utils.validators import get_model

        try:
            Person = get_model('person', 'Person')
        except LookupError:
            Person = None

        if Person:
            post_save.connect(person_handler, sender=Person)
            m2m_changed.connect(person_roles_handler, sender=Person.roles.through)

        try:
            Attribute = get_model('person', 'Attribute')
        except LookupError:
            Attribute = None

        if Attribute:
            post_save.connect(attribute_handler, sender=Attribute)
