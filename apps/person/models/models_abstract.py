import uuid

from django.conf import settings
from django.db import models
from django.contrib.contenttypes.fields import (
    GenericForeignKey, GenericRelation)
from django.utils.translation import ugettext_lazy as _
from django.core.validators import RegexValidator


class AbstractRole(models.Model):
    """ Collection roles for user """
    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    label = models.CharField(max_length=255)
    identifier = models.SlugField(
        _('Identifier'), max_length=168, unique=True,
        validators=[
            RegexValidator(
                regex=r'^[a-zA-Z_][0-9a-zA-Z_]*$',
                message=_(
                    "Identifier only contain the letters a-z, A-Z, digits, "
                    "and underscores, and can't start with a digit."))],
        help_text=_("Identifier used for looking up conditional."))
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    is_default = models.BooleanField(default=False, null=True)

    class Meta:
        abstract = True
        app_label = 'person'
        unique_together = ['identifier', 'is_default']
        verbose_name = _('Role')
        verbose_name_plural = _('Roles')

    def __str__(self):
        return '%s : %s' % (self.identifier, self.label)

    def save(self, *args, **kwargs):
        self.identifier = self.identifier.lower()
        return super().save(*args, **kwargs)


class AbstractPerson(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True, blank=True,
        related_name='person'
    )
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    roles = models.ManyToManyField('person.Role', related_name='roles')
    attribute_values = GenericRelation(
        'person.AttributeValue',
        related_query_name='person')
    options = models.ManyToManyField(
        'person.Option', blank=True, verbose_name=_("Options"))

    class Meta:
        abstract = True
        app_label = 'person'
        ordering = ['-user__date_joined']
        verbose_name = _("Person")
        verbose_name_plural = _("Persons")

    def __str__(self):
        return self.user.username


class AbstractOption(models.Model):
    """
    An option for user
    Example is user validate email? Or validate phone? Or other...
    """
    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    label = models.CharField(_("Label"), max_length=128)
    identifier = models.SlugField(
        _('Identifier'), max_length=128, unique=True,
        validators=[
            RegexValidator(
                regex=r'^[a-zA-Z_][0-9a-zA-Z_]*$',
                message=_(
                    "Identifier only contain the letters a-z, A-Z, digits, "
                    "and underscores, and can't start with a digit."))],
        help_text=_("Identifier used for looking up conditional."))

    REQUIRED, OPTIONAL = (1, 0)
    TYPE_CHOICES = (
        (REQUIRED, _("Required - a value for this option must be specified")),
        (OPTIONAL, _("Optional - a value for this option can be omitted")),
    )
    required = models.PositiveIntegerField(
        _("Status"), default=REQUIRED, choices=TYPE_CHOICES)

    class Meta:
        abstract = True
        app_label = 'person'
        verbose_name = _("Option")
        verbose_name_plural = _("Options")

    def __str__(self):
        return self.label

    @property
    def is_required(self):
        return self.required == self.REQUIRED
