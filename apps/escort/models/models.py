from django.db import models

from .models_abstract import *
from .models_attribute import *
from utils.validators import is_model_registered

__all__ = list()


# 0
if not is_model_registered('escort', 'Media'):
    class Media(AbstractMedia):
        class Meta(AbstractMedia.Meta):
            db_table = 'escort_media'

    __all__.append('Media')


# 1
if not is_model_registered('escort', 'Responsible'):
    class Responsible(AbstractResponsible):
        class Meta(AbstractResponsible.Meta):
            db_table = 'escort_responsible'

    __all__.append('Responsible')


# 2
if not is_model_registered('escort', 'Rating'):
    class Rating(AbstractRating):
        class Meta(AbstractRating.Meta):
            db_table = 'escort_rating'

    __all__.append('Rating')


# 3
if not is_model_registered('escort', 'Option'):
    class Option(AbstractOption):
        class Meta(AbstractOption.Meta):
            db_table = 'escort_option'

    __all__.append('Option')


# 4
if not is_model_registered('escort', 'Attachment'):
    class Attachment(AbstractAttachment):
        class Meta(AbstractAttachment.Meta):
            db_table = 'escort_attachment'

    __all__.append('Attachment')


# 5
if not is_model_registered('escort', 'Protest'):
    class Protest(AbstractProtest):
        class Meta(AbstractProtest.Meta):
            db_table = 'escort_protest'

    __all__.append('Protest')


# 6
if not is_model_registered('escort', 'Comment'):
    class Comment(AbstractComment):
        class Meta(AbstractComment.Meta):
            db_table = 'escort_comment'

    __all__.append('Comment')


# 7
if not is_model_registered('escort', 'AttributeOptionGroup'):
    class AttributeOptionGroup(AbstractAttributeOptionGroup):
        class Meta(AbstractAttributeOptionGroup.Meta):
            db_table = 'escort_attribute_option_group'

    __all__.append('AttributeOptionGroup')


# 8
if not is_model_registered('escort', 'AttributeOption'):
    class AttributeOption(AbstractAttributeOption):
        class Meta(AbstractAttributeOption.Meta):
            db_table = 'escort_attribute_option'

    __all__.append('AttributeOption')


# 9
if not is_model_registered('escort', 'Attribute'):
    class Attribute(AbstractAttribute):
        class Meta(AbstractAttribute.Meta):
            db_table = 'escort_attribute'

    __all__.append('Attribute')


# 10
if not is_model_registered('escort', 'AttributeValue'):
    class AttributeValue(AbstractAttributeValue):
        class Meta(AbstractAttributeValue.Meta):
            db_table = 'escort_attribute_value'

    __all__.append('AttributeValue')


# 11
if not is_model_registered('escort', 'EntityLog'):
    class EntityLog(AbstractEntityLog):
        class Meta(AbstractEntityLog.Meta):
            db_table = 'escort_entity_log'

    __all__.append('EntityLog')


# 12
if not is_model_registered('escort', 'Thumbed'):
    class Thumbed(AbstractThumbed):
        class Meta(AbstractThumbed.Meta):
            db_table = 'escort_thumbed'

    __all__.append('Thumbed')
