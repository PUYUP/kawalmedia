import uuid
import asyncio
import urllib
import json

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import (
    PasswordResetTokenGenerator,
    default_token_generator
)
from django.core.exceptions import ObjectDoesNotExist
from django.utils import six
from django.utils.http import (
    urlsafe_base64_encode,
    urlsafe_base64_decode
)
from django.utils.encoding import force_bytes
from django.utils.translation import ugettext_lazy as _

from .senders import (
    send_verification_email,
    send_verification_sms,
    send_password_email,
    send_secure_email
)

UserModel = get_user_model()
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)


def check_verified_email(self, *args, **kwargs):
    """ Check person validate email status """
    person = kwargs.get('person', None)
    if person is None:
        return None

    # Check person verified_email or not
    # The 'verified_email' is identifier set in Person Options
    try:
        is_verified_email = person.options.get(identifier='verified_email')
    except ObjectDoesNotExist:
        is_verified_email = None
    return True if is_verified_email else False


def check_verified_phone(self, *args, **kwargs):
    """ Check person validate telephone status """
    person = kwargs.get('person', None)
    if person is None:
        return None

    # Check person verified_phone or not
    # The 'verified_phone' is identifier set in Person Options
    try:
        is_verified_phone = person.options.get(identifier='verified_phone')
    except ObjectDoesNotExist:
        is_verified_phone = None
    return True if is_verified_phone else False


class TokenGenerator(PasswordResetTokenGenerator):
    def _make_hash_value(self, person, timestamp):
        # Check person verified mail and telp or not
        # The 'verified_email' and 'verified_phone' from Person Options
        is_verified_email = check_verified_email(self, person=person)
        is_verified_phone = check_verified_phone(self, person=person)
        return (
            six.text_type(person.uuid) + six.text_type(timestamp) +
            six.text_type(is_verified_email) + six.text_type(is_verified_phone)
        )


account_verification_token = TokenGenerator()


def random_string():
    """ Global verification code """
    length = 6
    code = uuid.uuid4().hex
    code = code.upper()[0:length]
    return code


def get_user(self, email):
    """Given an email, return matching user(s)
    who should receive a secure code."""
    if email:
        try:
            user = UserModel.objects.get(email=email)
        except ObjectDoesNotExist:
            user = None
        return user
    return None


def get_user_with_uuid(self, uuid_init=None):
    """Get person object by uuid"""
    if uuid_init is None:
        return None

    try:
        uuid_init = uuid.UUID(uuid_init)
    except ValueError:
        return None

    try:
        user = UserModel.objects.get(person__uuid=uuid_init)
    except ObjectDoesNotExist:
        user = None
    return user


def get_person_uuid(self, secure_code=None):
    """Get person uuid from secure code
    In session person uuid is encryped"""
    if secure_code is None:
        return None

    session = self.request.session.get(secure_code, None)
    if session is None:
        return None

    try:
        return force_bytes(urlsafe_base64_decode(session['uuid']))
    except KeyError:
        return None


def get_person(self, *args, **kwargs):
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
    identifier = kwargs.get('identifier', None)

    # If user loggedin
    if self.request.user.is_authenticated:
        user = self.request.user
    else:
        user = get_user(self, email)
        if user is None:
            return None

    # Person exist in user
    if hasattr(user, 'person'):
        context = {}
        tmpkey = 'KM_'.upper()
        delete_key = None
        person = user.person
        secure_code = '%s%s' % (tmpkey, random_string())

        # Return data
        context['uuid'] = urlsafe_base64_encode(force_bytes(person.uuid))
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
    if secure_code is None:
        return None

    session = self.request.session.get(secure_code, None)
    if session is None:
        return None

    person = get_person(self, secure_code=secure_code)
    token = session['token']
    return account_verification_token.check_token(person, token)


def send_secure_code(self, *agrs, **kwargs):
    """Send secure code to person
    This action required authentication
    Get user from request"""
    email = kwargs.get('email', None)
    telephone = kwargs.get('telephone', None)
    action = kwargs.get('action', None)
    identifier = kwargs.get('identifier', None)

    # Check email, telephone or action, this value required!
    if (not email or not telephone) and not action:
        return None

    # Get user
    if self.request.user.is_authenticated:
        user = self.request.user
    else:
        user = get_user(self, email)

    # Get person from user
    person = getattr(user, 'person', None)

    # Generate secure code
    secure_code = create_secure_code(self, email=email, identifier=identifier)
    if not secure_code:
        return None

    # Collect data for email
    verification_data = {
        'user': person.user,
        'email': email,
        'telephone': telephone,
        'request': self.request,
    }

    # Send secure code for verification (used for new registered user)
    if action == 'account_verification':
        # Check person verified mail, telp or not
        # Send verification to mail
        if email:
            is_verified_email = check_verified_email(self, person=person)

        if email and is_verified_email is False:
            # Send email!
            loop.run_in_executor(
                None, send_verification_email, verification_data)
            return secure_code

        # Send verification to telephone
        if telephone:
            is_verified_phone = check_verified_phone(self, person=person)

        if telephone and is_verified_phone is False:
            # Send SMS
            loop.run_in_executor(
                None, send_verification_sms, verification_data)
            return secure_code

    # Reset password
    if action == 'password_request':
        # Reset by email
        if settings.AUTH_VERIFICATION_METHOD == 0:
            # Send email!
            loop.run_in_executor(None, send_password_email, verification_data)
        return secure_code

    # Secure action
    if action == 'secure_validation':
        if settings.AUTH_VERIFICATION_METHOD == 0:
            # Send email!
            loop.run_in_executor(None, send_secure_email, verification_data)
        return secure_code
    return None
