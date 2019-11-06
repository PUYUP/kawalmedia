from django.utils.translation import ugettext_lazy as _

# Field types
TEXT = "text"
EMAIL = "email"
URL = "url"
INTEGER = "integer"
BOOLEAN = "boolean"
FLOAT = "float"
RICHTEXT = "richtext"
DATE = "date"
DATETIME = "datetime"
OPTION = "option"
MULTI_OPTION = "multi_option"
FILE = "file"
IMAGE = "image"
FIELD_TYPE_CHOICES = (
    (TEXT, _("Text")),
    (EMAIL, _("Email")),
    (URL, _("URL")),
    (INTEGER, _("Integer")),
    (BOOLEAN, _("True / False")),
    (FLOAT, _("Float")),
    (RICHTEXT, _("Rich Text")),
    (DATE, _("Date")),
    (DATETIME, _("Datetime")),
    (OPTION, _("Option")),
    (MULTI_OPTION, _("Multi Option")),
    (FILE, _("File")),
    (IMAGE, _("Image")),
)

FIELD_VALIDATION_CHOICES = (
    (TEXT, _("Text")),
    (EMAIL, _("Email")),
    (URL, _("URL")),
    (INTEGER, _("Integer")),
    (RICHTEXT, _("Rich Text")),
    (FILE, _("File")),
    (IMAGE, _("Image")),
)

MANUAL = 0
AUTO = 1
VERIFICATION_METHOD = (
    (AUTO, _("Auto")),
    (MANUAL, _("Manual")),
)
