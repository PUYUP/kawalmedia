from django import forms
from django.contrib.auth import get_user_model
from django.forms.models import BaseModelForm, BaseInlineFormSet
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.forms import UserCreationForm, UserChangeForm

from utils.validators import get_model

Person = get_model('person', 'Person')
Role = get_model('person', 'Role')
AttributeOptionGroup = get_model('person', 'AttributeOptionGroup')
UserModel = get_user_model()


class UserChangeForm(UserChangeForm):
    """ Override user Edit form """
    email = forms.EmailField(max_length=254, help_text=_(
        "Required. Inform a valid email address."))
    roles = forms.ModelMultipleChoiceField(queryset=None)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        current_roles_obj = None
        try:
            person_obj = Person.objects.get(user__pk=self.instance.pk)
            current_roles_obj = person_obj.roles.all()
        except Person.DoesNotExist:
            current_roles_obj = None
        self.fields['roles'].queryset = Role.objects.filter(is_active=True)
        self.fields['roles'].initial = current_roles_obj

    def clean_email(self):
        email = self.cleaned_data.get('email', None)
        username = self.cleaned_data.get('username', None)

        # Make user email filled
        if email and email is not None:
            # Validate each account has different email
            if UserModel.objects.filter(email=email).exclude(
                    username=username).exists():
                raise forms.ValidationError(_('Email has been used.'))
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        if commit:
            user.save()

        if user and user is not None:
            roles_obj = self.cleaned_data['roles']
            if hasattr(user, 'person'):
                person_obj = Person.objects.get(user_id=user.pk)
                person_obj.roles.set(roles_obj)
            else:
                person_obj = Person.objects.create(user_id=user.pk)
                person_obj.roles.add(*roles_obj)
            person_obj.save()
        return user


class UserCreationForm(UserCreationForm):
    """ Override user Add form """
    email = forms.EmailField(max_length=254, help_text=_(
        "Required. Inform a valid email address."))
    roles = forms.ModelMultipleChoiceField(queryset=None)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['roles'].queryset = Role.objects.filter(is_active=True)

    def clean_email(self):
        email = self.cleaned_data.get('email', None)
        username = self.cleaned_data.get('username', None)

        # Make user email filled
        if email and email is not None:
            # Validate each account has different email
            if UserModel.objects.filter(email=email).exclude(
                    username=username).exists():
                raise forms.ValidationError(
                    _('Email has been used.'),
                    code='email_used',
                )
        return email

    def save(self, commit=True):
        user = super().save(commit=True)
        if commit:
            user.save()

        if user and user is not None:
            roles_obj = self.cleaned_data['roles']
            try:
                person_obj = Person.objects.create(user_id=user.pk)
            except Person.DoesNotExist:
                person_obj = None

            if person_obj is not None:
                person_obj.roles.add(*roles_obj)
                person_obj.save()
        return user


class ChildInlineFormSet(BaseInlineFormSet):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Now we need to make a queryset to each field of each form inline
        self.queryset = None


class AttributeValueForm(forms.ModelForm):
    value_multi_option = forms.ModelMultipleChoiceField(
        required=False, queryset=None)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        attributes = AttributeOptionGroup.objects.all()
        self.fields['value_multi_option'].queryset = attributes

    def clean_value_multi_option(self):
        pass
