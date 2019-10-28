from django.contrib import admin
from django.utils.translation import ugettext_lazy as _
from django.utils.html import format_html
from django.contrib.auth import get_user_model
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.contenttypes.admin import GenericStackedInline
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.forms import (
    BaseGenericInlineFormSet, generic_inlineformset_factory,
)

# Project UTILS
from utils.validators import get_model

UserModel = get_user_model()
Person = get_model('person', 'Person')
Attachment = get_model('escort', 'Attachment')
Media = get_model('escort', 'Media')
Rating = get_model('escort', 'Rating')
Protest = get_model('escort', 'Protest')
Comment = get_model('escort', 'Comment')
Responsible = get_model('escort', 'Responsible')
EntityLog = get_model('escort', 'EntityLog')
Thumbed = get_model('escort', 'Thumbed')

Option = get_model('escort', 'Option')
AttributeOptionGroup = get_model('escort', 'AttributeOptionGroup')
AttributeOption = get_model('escort', 'AttributeOption')
Attribute = get_model('escort', 'Attribute')
AttributeValue = get_model('escort', 'AttributeValue')


"""All inlines define start here"""


class AttachmentFormset(BaseGenericInlineFormSet):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.queryset.prefetch_related(
            'uploader', 'uploader__user', 'content_type') \
            .select_related('uploader', 'uploader__user', 'content_type')


class AttachmentInline(GenericStackedInline):
    model = Attachment
    formset = AttachmentFormset

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.prefetch_related('uploader', 'content_type') \
            .select_related('uploader', 'content_type')


class AttributeOptionInline(admin.TabularInline):
    model = AttributeOption


"""All admin extend start here"""


class MediaAdmin(admin.ModelAdmin):
    """Extend media admin"""
    model = Media
    readonly_fields = ('classification',)
    list_display = ('label', 'classification', 'publication', 'status',
                    'creator', 'date_created', 'date_updated',)

    def formfield_for_dbfield(self, db_field, **kwargs):
        # Modification publication field
        if db_field.name == 'publication':
            choices = db_field.choices
            new_choices = list()

            for choice in choices:
                c = [thing for thing in choice]
                key = c[0]
                value = c[1]

                if type(key) == tuple:
                    new_choices.append((key[1], value))
                else:
                    new_choices.append((key, value))
            db_field.choices = new_choices
        return super().formfield_for_dbfield(db_field, **kwargs)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'creator':
            kwargs['queryset'] = Person.objects.prefetch_related('user') \
                .select_related('user')
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.prefetch_related('creator') \
            .select_related('creator')

    def save_model(self, request, obj, form, change):
        # Append request to signals
        setattr(obj, 'request', request)
        super().save_model(request, obj, form, change)


class RatingAdmin(admin.ModelAdmin):
    """Extend media rating admin"""
    model = Rating
    list_display = ('media', 'rater', 'score', 'date_created',)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'rater':
            kwargs['queryset'] = Person.objects.prefetch_related('user') \
                .select_related('user')
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.prefetch_related('media', 'rater', 'rater__user') \
            .select_related('media', 'rater', 'rater__user')

    def save_model(self, request, obj, form, change):
        # Append request to signals
        setattr(obj, 'request', request)
        super().save_model(request, obj, form, change)


class ProtestAdmin(admin.ModelAdmin):
    """Extend media protest admin"""
    model = Protest
    list_display = ('label', 'media', 'protester', 'status', 'date_created',)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'protester':
            kwargs['queryset'] = Person.objects.prefetch_related('user') \
                .select_related('user')
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.prefetch_related('protester', 'media') \
            .select_related('protester', 'media')

    def save_model(self, request, obj, form, change):
        # Append request to signals
        setattr(obj, 'request', request)
        super().save_model(request, obj, form, change)


class CommentAdmin(admin.ModelAdmin):
    """Extend protest comment admin"""
    model = Comment
    list_display = ('protest', 'parent', 'commenter',
                    'description', 'date_created',)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'commenter' or db_field.name == 'reply_for_person':
            kwargs['queryset'] = Person.objects.prefetch_related('user') \
                .select_related('user')

        if db_field.name == 'parent' or db_field.name == 'reply_to_comment':
            kwargs['queryset'] = Comment.objects.prefetch_related(
                'protest', 'commenter__user', 'reply_for_person__user', 'parent') \
                .select_related('protest', 'commenter__user', 'reply_for_person__user', 'parent')

        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.prefetch_related('protest', 'commenter__user', 'parent',
                                   'reply_for_person__user', 'reply_to_comment__parent') \
            .select_related('protest', 'commenter__user', 'parent',
                            'reply_for_person__user', 'reply_to_comment__parent')

    def save_model(self, request, obj, form, change):
        # Append request to signals
        setattr(obj, 'request', request)
        super().save_model(request, obj, form, change)


class ResponsibleAdmin(admin.ModelAdmin):
    """Extend Responsible admin"""
    model = Responsible
    list_display = ('media', 'responser', 'date_created',)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'responser':
            kwargs['queryset'] = Person.objects.prefetch_related('user') \
                .select_related('user')
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.prefetch_related('media', 'responser', 'responser__user') \
            .select_related('media', 'responser', 'responser__user')

    def save_model(self, request, obj, form, change):
        # Append request to signals
        setattr(obj, 'request', request)
        super().save_model(request, obj, form, change)


class OptionAdmin(admin.ModelAdmin):
    """Extend option admin"""
    model = Option
    prepopulated_fields = {"identifier": ("label", )}

    def save_model(self, request, obj, form, change):
        # Append request to signals
        setattr(obj, 'request', request)
        super().save_model(request, obj, form, change)


class AttributeAdmin(admin.ModelAdmin):
    """Extend attributes admin"""
    model = Attribute
    list_display = ('label', 'identifier', 'type', 'entity_type',)
    prepopulated_fields = {"identifier": ("label", )}

    def entity_type(self, obj):
        if obj.content_type:
            entity_html = []
            entities = obj.content_type.all()
            for entity in entities:
                entity_item = format_html('{}',entity)
                entity_html.append(entity_item)
            return entity_html
        else:
            return None
    entity_type.short_description = _("Entity type")


class AttributeOptionGroupAdmin(admin.ModelAdmin):
    """Extend AttributeOptionGroup admin"""
    model = AttributeOptionGroup
    inlines = (AttributeOptionInline,)
    prepopulated_fields = {"identifier": ("label", )}


class AttributeValueAdmin(admin.ModelAdmin):
    """Extend AttributeValue admin"""
    model = AttributeValue
    list_display = ('entity', 'attribute', 'entity_type', 'value',)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.prefetch_related('attribute', 'attribute__option_group',
                                   'value_option', 'content_type') \
            .select_related('attribute', 'attribute__option_group',
                            'value_option', 'content_type')

    def entity_type(self, obj):
        if obj.content_type:
            return obj.content_type
        else:
            return None
    entity_type.short_description = _("Entity type")

    def entity(self, obj):
        if obj.content_object:
            return obj.content_object.label
        else:
            return None
    entity.short_description = _("Entity object")


class EntityLogAdmin(admin.ModelAdmin):
    """Extend EntityLog admin"""
    model = EntityLog
    list_display = ('get_label', 'get_entity', 'status',)

    def get_label(self, obj):
        label = getattr(obj.content_object, 'label', None)
        if not label:
            label = getattr(obj.content_object, 'user', None)
        return label
    get_label.short_description = _("Label")

    def get_entity(self, obj):
        return obj.content_type
    get_entity.short_description = _("Entity")


class ThumbedAdmin(admin.ModelAdmin):
    """Extend Thumbed admin"""
    model = Thumbed
    list_display = ('thumber', 'content_object', 'get_entity', 'thumbing',)

    def get_entity(self, obj):
        return obj.content_type
    get_entity.short_description = _("Entity")


# Register your models here.
admin.site.register(Media, MediaAdmin)
admin.site.register(Rating, RatingAdmin)
admin.site.register(Protest, ProtestAdmin)
admin.site.register(Comment, CommentAdmin)

admin.site.register(Option, OptionAdmin)
admin.site.register(AttributeOptionGroup, AttributeOptionGroupAdmin)
admin.site.register(Attribute, AttributeAdmin)
admin.site.register(AttributeValue, AttributeValueAdmin)

admin.site.register(Attachment)
admin.site.register(Responsible, ResponsibleAdmin)
admin.site.register(EntityLog, EntityLogAdmin)
admin.site.register(Thumbed, ThumbedAdmin)
