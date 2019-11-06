import uuid
import asyncio
import urllib
import json

from django.conf import settings
from django.db.models import Q
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import (
    PasswordResetTokenGenerator,
    default_token_generator)
from django.core.exceptions import ObjectDoesNotExist
from django.utils import six
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.utils.translation import ugettext_lazy as _

# PROJECT UTILS
from utils.validators import get_model

from .senders import (
    send_verification_email,
    send_verification_sms,
    send_password_email,
    send_secure_email
)

Validation = get_model('person', 'Validation')
ValidationValue = get_model('person', 'ValidationValue')
UserModel = get_user_model()
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)


def check_validation_passed(self, *agrs, **kwargs):
    request = kwargs.get('request', None)
    if not request:
        return False

    person = getattr(request.user, 'person', None)
    if not person:
        return False

    content_type = ContentType.objects.get_for_model(person)
    validation_type = Validation.objects.filter(required=True)

    if not validation_type.exists():
        return True

    validation_value = ValidationValue.objects.filter(
        Q(validation__required=True),
        Q(verified=True),
        Q(content_type=content_type.pk),
        Q(object_id=person.pk))

    # Compare validation type with the value
    # If value same indicated all validation passed
    return validation_type.count() == validation_value.count()


class TokenGenerator(PasswordResetTokenGenerator):
    def _make_hash_value(self, person, timestamp):
        return (
            six.text_type(person.uuid) + six.text_type(timestamp)
        )


account_verification_token = TokenGenerator()


def random_string():
    """ Global verification code """
    length = 6
    code = uuid.uuid4().hex
    code = code.upper()[0:length]
    return code


def get_user_from_email(self, email=None):
    """Given an email, return matching user(s)
    who should receive a secure code."""
    if email:
        try:
            user = UserModel.objects.get(email=email)
        except ObjectDoesNotExist:
            user = None
        return user
    return None


def get_user_from_uuid(self, person_uuid=None):
    """Get person object by uuid"""
    if person_uuid is None:
        return None

    try:
        person_uuid = uuid.UUID(person_uuid)
    except ValueError:
        return None

    try:
        user = UserModel.objects.get(person__uuid=person_uuid)
    except ObjectDoesNotExist:
        user = None
    return user


def get_person_uuid(self, secure_code=None):
    """Get person uuid from secure code
    In session person uuid is encryped"""
    if not secure_code:
        return None

    session = self.request.session.get(secure_code, None)
    if not session:
        return None

    try:
        return force_bytes(urlsafe_base64_decode(session['person_uuid']))
    except KeyError:
        return None


def get_person_from_secure_code(self, *args, **kwargs):
    """Get person from secure code"""
    secure_code = kwargs.get('secure_code', None)
    if secure_code is None:
        return None

    person_uuid = get_person_uuid(self, secure_code=secure_code)
    if person_uuid is None:
        return None

    person_uuid = str(person_uuid, 'utf-8')
    person_uuid = uuid.UUID(person_uuid)

    # Now get person by uuid
    try:
        user = UserModel.objects.get(person__uuid=person_uuid)
    except ObjectDoesNotExist:
        return None

    if hasattr(user, 'person'):
        return user.person
    return None


def create_secure_code(self, *args, **kwargs):
    """Generate secure code, make sure we check from user by email"""
    email = kwargs.get('email', None)

    # Get user from email if not logged in
    if self.request.user.is_authenticated:
        user = self.request.user
    else:
        user = get_user_from_email(self, email)
        if user is None:
            return None

    # Person exist in user
    if hasattr(user, 'person'):
        context = dict()
        tmpkey = 'KM'.upper()
        delete_key = None
        person = user.person
        secure_code = '%s%s' % (tmpkey, random_string())

        # Return data
        context['person_uuid'] = urlsafe_base64_encode(
            force_bytes(person.uuid))
        context['token'] = account_verification_token.make_token(person)
        context['secure_code'] = secure_code

        # Append secure code to request
        setattr(self.request, 'secure_code', secure_code)
        setattr(self.request, 'person', person)

        # Get cache from session
        session_cache = self.request.session._session_cache

        # Find session with tmpkey
        for key in session_cache:
            if tmpkey in key:
                delete_key = key

        # Delete previous session with key
        if delete_key:
            del self.request.session[delete_key]

        # Make and save data to session
        self.request.session.modified = True
        self.request.session[secure_code] = context
        return context
    return None


def validate_secure_code(self, *agrs, **kwargs):
    """Validate secure code valid or not"""
    secure_code = kwargs.get('secure_code', None)
    is_password_request = kwargs.get('is_password_request', None)

    if not secure_code:
        return None

    session = self.request.session.get(secure_code, None)
    if session is None:
        return None

    person = get_person_from_secure_code(self, secure_code=secure_code)
    token = session['token']

    # Prevent re-used delete from session
    # But if password request, hold it
    if not is_password_request:
        del self.request.session[secure_code]
    return account_verification_token.check_token(person, token)


def send_secure_code(self, *args, **kwargs):
    # Email or SMS
    # 1 = Email, 2 = SMS
    method = kwargs.get('method', None)
    email = kwargs.get('email', None)
    new_value = kwargs.get('new_value', None)
    user = kwargs.get('user', None)

    if not method and not user:
        return None

    person = getattr(user, 'person', None)
    if person:
        # Generate secure code
        # Whatever method, email used for check use exist
        secure_data = create_secure_code(self, email=email)
        if not secure_data:
            return None

        # Collect data for email
        params = {
            'user': user,
            'request': self.request,
            'email': email,
            'new_value': new_value,
            'label': _("Verifikasi")
        }

        # Send with email
        if method == 1:
            loop.run_in_executor(None, send_verification_email, params)

        # Send with SMS
        if method == 2:
            loop.run_in_executor(None, send_verification_sms, params)

        return secure_data
    return None
