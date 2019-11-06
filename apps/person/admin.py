from django.utils.translation import ugettext_lazy as _
from django.utils.html import format_html
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from utils.validators import get_model
from .utils.forms import (
    UserChangeForm,
    UserCreationForm,
    AttributeValueForm
)

User = get_model('auth', 'User')
Person = get_model('person', 'Person')
Role = get_model('person', 'Role')

AttributeOption = get_model('person', 'AttributeOption')
AttributeOptionGroup = get_model('person', 'AttributeOptionGroup')
Option = get_model('person', 'Option')
Attribute = get_model('person', 'Attribute')
AttributeValue = get_model('person', 'AttributeValue')
Validation = get_model('person', 'Validation')
ValidationValue = get_model('person', 'ValidationValue')


"""All inlines define start here"""


class AttributeOptionInline(admin.TabularInline):
    model = AttributeOption


class AttributeInline(admin.TabularInline):
    model = AttributeValue
    extra = 1

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.prefetch_related('attribute', 'person__user', 'value_option',
                                   'entity_content_type',
                                   'attribute__option_group') \
            .select_related('attribute', 'person__user', 'value_option',
                            'entity_content_type', 'attribute__option_group')


"""All admin extend start here"""


class UserAdmin(UserAdmin):
    form = UserChangeForm
    add_form = UserCreationForm
    fieldsets = (
        (None, {'fields': ('username', 'password', 'email')}),
        (_("Personal info"), {'fields': ('first_name', 'last_name',)}),
        (_("Permissions"), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'roles'),
        }),
        (_("Important dates"), {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1',
                       'password2', 'roles',)
        }),
    )


class RoleAdmin(admin.ModelAdmin):
    model = Role
    list_display = ('label', 'is_default', 'is_active',)
    prepopulated_fields = {"identifier": ("label", )}


class AttributeAdmin(admin.ModelAdmin):
    model = Attribute
    list_display = ('label', 'identifier', 'field_type',
                    'get_roles', 'entity_type', 'required',)
    prepopulated_fields = {"identifier": ("label", )}

    def get_roles(self, obj):
        """ Print all roles """
        if hasattr(obj, 'roles'):
            role_html = list()
            roles_obj = obj.roles.all()
            for role in roles_obj:
                role_item = format_html('{} : {}', role.identifier, role.label)
                role_html.append(role_item)
            return role_html
        return None
    get_roles.short_description = _('Roles')

    def entity_type(self, obj):
        if obj.content_type:
            ent_html = list()
            entities = obj.content_type.all()
            for ent in entities:
                ent_item = format_html('{}', ent)
                ent_html.append(ent_item)
            return ent_html
        else:
            return None
    entity_type.short_description = _("Entity type")


class OptionAdmin(admin.ModelAdmin):
    prepopulated_fields = {"identifier": ("label", )}


class AttributeValueAdmin(admin.ModelAdmin):
    model = AttributeValue
    list_display = ('entity', 'attribute', 'entity_type', 'value',)

    def entity_type(self, obj):
        if obj.content_type:
            return obj.content_type
        else:
            return None
    entity_type.short_description = _("Entity type")

    def entity(self, obj):
        if obj.content_object:
            return obj.content_object
        else:
            return None
    entity.short_description = _("Entity object")

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.prefetch_related(
            'attribute', 'attribute__option_group',
            'value_option', 'content_type') \
            .select_related(
                'attribute', 'attribute__option_group',
                'value_option', 'content_type')


class AttributeOptionGroupAdmin(admin.ModelAdmin):
    list_display = ('label',)
    inlines = [AttributeOptionInline]
    prepopulated_fields = {"identifier": ("label", )}


class PersonAdmin(admin.ModelAdmin):
    model = Person
    list_display = ('user',)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'person':
            kwargs['queryset'] = Person.objects.prefetch_related('user') \
                .select_related('user')
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.prefetch_related('user') \
            .select_related('user')

    def get_roles(self, obj):
        """ Print all roles """
        if hasattr(obj, 'roles'):
            role_html = list()
            roles_obj = obj.roles.all()
            for role in roles_obj:
                role_item = format_html('{} : {}', role.identifier, role.label)
                role_html.append(role_item)
            return role_html
        return None
    get_roles.short_description = _('Roles')


# Validation entity here


class ValidationAdmin(admin.ModelAdmin):
    model = Validation
    list_display = ('label', 'identifier', 'field_type',
                    'get_roles', 'entity_type',)
    prepopulated_fields = {"identifier": ("label", )}

    def get_roles(self, obj):
        """ Print all roles """
        if hasattr(obj, 'roles'):
            role_html = list()
            roles_obj = obj.roles.all()
            for role in roles_obj:
                role_item = format_html('{} : {}', role.identifier, role.label)
                role_html.append(role_item)
            return role_html
        return None
    get_roles.short_description = _('Roles')

    def entity_type(self, obj):
        if obj.content_type:
            ent_html = list()
            entities = obj.content_type.all()
            for ent in entities:
                ent_item = format_html('{}', ent)
                ent_html.append(ent_item)
            return ent_html
        else:
            return None
    entity_type.short_description = _("Entity type")


class ValidationValueAdmin(admin.ModelAdmin):
    model = ValidationValue
    list_display = ('entity', 'validation', 'entity_type',
                    'value', 'secure_code', 'verified', 'date_created',)
    list_filter = ('validation', 'verified', 'date_created',)
    search_fields = ('person__user__username',)

    def entity_type(self, obj):
        if obj.content_type:
            return obj.content_type
        else:
            return None
    entity_type.short_description = _("Entity type")

    def entity(self, obj):
        if obj.content_object:
            return obj.content_object
        else:
            return None
    entity.short_description = _("Entity object")

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.prefetch_related(
            'validation', 'content_type') \
            .select_related(
                'validation', 'content_type')

    def get_search_results(self, request, queryset, search_term):
        queryset, use_distinct = super().get_search_results(request, queryset, search_term)
        return queryset, use_distinct


# Register your models here.
admin.site.unregister(User)
admin.site.register(User, UserAdmin)
admin.site.register(Person, PersonAdmin)
admin.site.register(Role, RoleAdmin)

# Attributes
admin.site.register(Attribute, AttributeAdmin)
admin.site.register(AttributeValue, AttributeValueAdmin)
admin.site.register(AttributeOptionGroup, AttributeOptionGroupAdmin)
admin.site.register(Option, OptionAdmin)

# Validations
admin.site.register(Validation, ValidationAdmin)
admin.site.register(ValidationValue, ValidationValueAdmin)
