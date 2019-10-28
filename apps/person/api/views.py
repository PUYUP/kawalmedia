from uuid import UUID
from itertools import chain

from django.http import Http404
from django.contrib.auth import get_user_model
from django.db.models import F, Q, Value, Case, When, CharField
from django.db import transaction
from django.utils.translation import ugettext_lazy as _
from django.utils.decorators import method_decorator
from django.core.exceptions import ObjectDoesNotExist
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie
from django.contrib.sessions.backends.db import SessionStore
from django.views.decorators.cache import never_cache
from django.contrib.contenttypes.models import ContentType

# THIRD PARTY
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.parsers import (
    FormParser, FileUploadParser, MultiPartParser)
from rest_framework import status, viewsets
from rest_framework.pagination import PageNumberPagination
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, NotAcceptable

# JWT --> https://github.com/davesque/django-rest-framework-simplejwt
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView
)

# SERIALIZERS
from .serializers import (
    PersonSerializer,
    CreateSerializer,
    SingleSerializer,
    AttributeSerializer
)

# PERMISSIONS
from .permissions import IsOwnerOrReject

# GET MODELS FROM GLOBAL UTILS
from utils.validators import get_model

# APP UTILITY
from ..utils.attributes import update_attribute_values
from ..utils.senders import send_verification_email, send_password_email
from ..utils.auths import (
    random_string,
    check_verified_email,
    check_verified_phone,
    send_secure_code,
    validate_secure_code,
    get_person,
    get_user_with_uuid
)

Person = get_model('person', 'Person')
Attribute = get_model('person', 'Attribute')
AttributeValue = get_model('person', 'AttributeValue')
Role = get_model('person', 'Role')
Option = get_model('person', 'Option')
UserModel = get_user_model()

# Define to avoid used ...().paginate__
PAGINATOR = PageNumberPagination()


class TokenObtainPairSerializerExtend(TokenObtainPairSerializer):
    """ Extend JWT token response """

    def validate(self, attrs):
        data = super().validate(attrs)
        person = getattr(self.user, 'person', None)
        if person:
            data['uuid'] = person.uuid
            data['username'] = self.user.username
            data['verified_email'] = check_verified_email(self, person=person)
            data['verified_phone'] = check_verified_phone(self, person=person)
        return data


class TokenObtainPairViewExtend(TokenObtainPairView):
    serializer_class = TokenObtainPairSerializerExtend

    @method_decorator(csrf_protect)
    @method_decorator(never_cache)
    @transaction.atomic
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)

        try:
            serializer.is_valid(raise_exception=True)
        except TokenError as e:
            raise InvalidToken(e.args[0])

        # For security reason, save token to session
        code = random_string()
        request.session[code] = {
            'refresh': serializer.validated_data['refresh'],
            'access': serializer.validated_data['access']
        }

        # Save code to localStorage
        serializer.validated_data['auth_code'] = code

        # Remove token
        serializer.validated_data.pop('refresh')
        serializer.validated_data.pop('access')
        return Response(serializer.validated_data, status=status.HTTP_200_OK)


@method_decorator(ensure_csrf_cookie, name='dispatch')
class PersonApiView(viewsets.ViewSet):
    lookup_field = 'uuid'
    permission_classes = (AllowAny,)
    parser_class = (FormParser, FileUploadParser, MultiPartParser,)
    permission_action = {
        # Disable update if not owner
        'partial_update': [IsOwnerOrReject]
    }

    def get_permissions(self):
        """
        Instantiates and returns
        the list of permissions that this view requires.
        """
        try:
            # return permission_classes depending on `action`
            return [permission() for permission in self.permission_action
                    [self.action]]
        except KeyError:
            # action is not set return default permission_classes
            return [permission() for permission in self.permission_classes]

    # Get a objects
    def get_object(self, uuid=None):
        """ Fetches objects """
        try:
            if uuid:
                try:
                    uuid = UUID(uuid)
                    return Person.objects.get(uuid=uuid)
                except ValueError:
                    raise Http404
            objs = Person.objects.prefetch_related('user') \
                .select_related('user') \
                .all()
            return objs
        except ObjectDoesNotExist:
            raise Http404

    # Return a response
    def get_response(self, serializer, serializer_parent=None):
        """ Output to endpoint """
        response = {}
        if serializer_parent is not None:
            response['user'] = serializer_parent.data

        response['count'] = PAGINATOR.page.paginator.count
        response['navigate'] = {
            'previous': PAGINATOR.get_previous_link(),
            'next': PAGINATOR.get_next_link()
        }
        response['results'] = serializer.data
        return Response(response, status=status.HTTP_200_OK)

    # All persons
    def list(self, request, format=None):
        """ View as item list """
        context = {'request': self.request}
        queryset = self.get_object()
        queryset_paginator = PAGINATOR.paginate_queryset(
            queryset, request)
        serializer = PersonSerializer(
            queryset_paginator, many=True, context=context)
        return self.get_response(serializer)

    # Single person
    def retrieve(self, request, uuid=None, format=None):
        """ View as single object """
        context = {'request': self.request}
        queryset = self.get_object(uuid)
        serializer = SingleSerializer(
            queryset, many=False, context=context)
        return Response(serializer.data, status=status.HTTP_200_OK)

    # Register user as person
    @method_decorator(csrf_protect)
    @method_decorator(never_cache)
    @transaction.atomic
    def create(self, request, format=None):
        """ Create single object """
        context = {'request': self.request}
        serializer = CreateSerializer(data=request.data, context=context)
        if serializer.is_valid(raise_exception=True):
            user = serializer.save()

            # Send email with verification code
            send_secure_code(
                self, email=user.email,
                action='account_verification')

            # The response
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # Update basic user data
    # Email, username, password, ect
    @transaction.atomic
    def partial_update(self, request, uuid=None, format=None):
        """ Update basic info """
        context = {'request': self.request}
        instance = self.get_object(uuid)
        serializer = SingleSerializer(
            instance, data=request.data, partial=True, context=context)

        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # Sub-action send email persons
    # We need send a verification code to new user
    # Or they can request new verification
    @method_decorator(csrf_protect)
    @method_decorator(never_cache)
    @transaction.atomic
    @action(methods=['post'], detail=False,
            permission_classes=[IsAuthenticated],
            url_path='verification', url_name='send_verification')
    def send_verification(self, request):
        """ Send verification for secured action """

        # Get saved session by secure code
        response = {}
        verification = request.data.get('verification', None)

        if verification:
            # Send email with verification code
            sc = send_secure_code(self, **request.data)
            if sc is not None and sc:
                response['detail'] = _('Verification code send.')
                return Response(response, status=status.HTTP_200_OK)
            raise NotAcceptable()
        raise NotFound()

    # Sub-action validate person
    @method_decorator(csrf_protect)
    @method_decorator(never_cache)
    @transaction.atomic
    @action(methods=['post'], detail=False,
            permission_classes=[IsAuthenticated],
            url_path='validation', url_name='perform_validation')
    def perform_validation(self, request):
        """Validate user with secure code
        ---------------
        JSON Format:
        {
            "secure_code": "1234IL"
        }"""

        response = {}
        secure_code = request.data.get('secure_code', None)
        action = request.data.get('action', None)
        verification = request.data.get('verification', None)

        # Important, secure code and action required!
        if secure_code and action:
            # Check session valid or not by secure code
            is_passed = validate_secure_code(self, secure_code=secure_code)
            if is_passed is None:
                raise NotFound(detail=_("Kode otentikasi tidak benar."))

            # Get person with secure code
            person = get_person(self, secure_code=secure_code)
            if person is None:
                raise NotFound()

            # Perform user validation after register
            if action == 'account_verification':
                # Check person verified_email or not
                is_verified_email = check_verified_email(self, person=person)
                is_verified_phone = check_verified_phone(self, person=person)

                # Separate verification type
                if verification == 'email':
                    if is_verified_email:
                        raise NotAcceptable()

                if verification == 'phone':
                    if is_verified_phone:
                        raise NotAcceptable()

                # Now change option
                if (
                    is_verified_email is False or is_verified_phone is False
                ) and is_passed:
                    try:
                        if verification == 'email':
                            option = Option.objects.get(
                                identifier='verified_email')

                        if verification == 'phone':
                            option = Option.objects.get(
                                identifier='verified_phone')
                    except ObjectDoesNotExist:
                        option = None

                    if option is not None:
                        person.options.add(option)
                    else:
                        raise NotAcceptable()
                response['detail'] = _('Account successful verified.')

            # General validation
            # Ex: upate password, email, or secured other data
            if action == 'secure_validation':
                pass
            return Response(response, status=status.HTTP_200_OK)
        raise NotAcceptable()

    # Sub-action request password reset
    @method_decorator(csrf_protect)
    @method_decorator(never_cache)
    @transaction.atomic
    @action(methods=['post'], detail=False, permission_classes=[AllowAny],
            url_path='password-request', url_name='password_request')
    def password_request(self, request):
        """ Request new password
        ---------------
        JSON Format:
        {
            "email": "my@email.com"
        } """

        response = {}
        email = request.data.get('email', None)
        secure_code = request.data.get('secure_code', None)
        action = request.data.get('action', None)

        # First request use email
        # And secure_code is none
        if (email is None or not email) and secure_code is None:
            raise NotFound(detail=_("Alamat email wajib."))

        # Send email with email
        if secure_code is not None:
            sc = send_secure_code(self, secure_code_init=secure_code,
                                  action=action)
        else:
            sc = send_secure_code(self, email=email, action=action)

        if sc is not None:
            response['detail'] = _("Periksa email Anda untuk instruksi lebih lanjut.")
            return Response(response, status=status.HTTP_200_OK)
        raise NotFound(detail=_("Akun tidak ditemukan."))

    # Sub-action request new password
    @method_decorator(csrf_protect)
    @method_decorator(never_cache)
    @transaction.atomic
    @action(methods=['post'], detail=False, permission_classes=[AllowAny],
            url_path='password-recovery', url_name='password_recovery')
    def password_recovery(self, request):
        """ Create new password
        ---------------
        JSON Format:
        {
            "password1": "new password",
            "password2": "new password",
            "secure_code": "123A87"
        } """

        response = {}
        secure_code = self.request.data.get('secure_code', None)
        password1 = self.request.data.get('password1', None)
        password2 = self.request.data.get('password2', None)
        is_passed = validate_secure_code(self, secure_code=secure_code)

        # Make sure session exist!
        if secure_code is not None:
            if password1 and password2:
                if password1 != password2:
                    raise NotAcceptable(
                        detail=_("Kata sandi tidak sama."),
                        code='password_mismatch',
                    )

            if is_passed and password1 and password2:
                person = get_person(self, secure_code=secure_code)
                if hasattr(person, 'user'):
                    user = person.user
                    user.set_password(password2)
                    user.save()
                    response = {'detail': _("Kata sandi berhasil diganti.")}
                    return Response(response, status=status.HTTP_200_OK)
            raise NotAcceptable()
        raise NotFound()

    # Sub-action logout
    @method_decorator(csrf_protect)
    @transaction.atomic
    @action(methods=['post'], detail=False,
            permission_classes=[IsAuthenticated],
            url_path='logout', url_name='perfom_logout')
    def perfom_logout(self, request):
        # Get saved session by verification code
        response = {}
        auth_code = self.request.data.get('auth_code', None)
        session_key = self.request.session.session_key

        if auth_code or session_key:
            # del self.request.session[auth_code]
            s = SessionStore(session_key=session_key)
            s.delete()
        return Response(auth_code, status=status.HTTP_200_OK)


class OptionApiView(viewsets.ViewSet):
    """ Get attribute options for persons
    Read only... """
    lookup_field = 'uuid'
    permission_classes = (IsAuthenticated,)
    parser_class = (FormParser, FileUploadParser, MultiPartParser,)
    permission_action = {
        # Disable update if not owner
        'update': [IsOwnerOrReject],
        'partial_update': [IsOwnerOrReject]
    }

    def list(self, request, format=None):
        response = {}
        context = {'request': self.request}
        identifiers = request.GET.get('identifiers', None)
        securities = request.GET.get('securities', None)
        person_uuid = request.GET.get('person_uuid', None)

        # Attributes view by other person
        if person_uuid:
            user = get_user_with_uuid(self, uuid_init=person_uuid)
            if user is None:
                raise NotAcceptable(detail=_("Data tidak valid."))
        else:
            user = request.user

        # Attributes
        if hasattr(user, 'person') and identifiers and securities is None:
            person = getattr(user, 'person', None)
            identifiers = identifiers.split(',')
            identifiers_exclude = identifiers

            # ContentType berdasarkan entity (model)
            entity_type = ContentType.objects.get_for_model(person)

            # Get roles from person
            roles = person.roles.filter(is_active=True) \
                .values_list('id', flat=True)

            # Get options by roles
            queryset = Attribute.objects \
                .filter(
                    content_type=entity_type,
                    roles__in=roles,
                    identifier__in=identifiers,
                    attributevalue__object_id=person.pk,
                    secured=False) \
                .prefetch_related('option_group') \
                .select_related('option_group') \
                .distinct()

            if queryset.exists():
                for qs in queryset:
                    identifiers_exclude.remove(qs.identifier)

                annotate = {}
                for q in queryset:
                    field = 'value_' + q.type
                    if q.type == 'multi_option':
                        annotate[field] = F('attributevalue')
                    else:
                        annotate[field] = F('attributevalue__%s' % field)

                # Call value each field
                queryset = queryset.annotate(**annotate)

            # Here we get all attributes
            # But filter by empty attributevalue
            queryset_all = Attribute.objects \
                .filter(
                    content_type=entity_type,
                    roles__in=roles,
                    identifier__in=identifiers_exclude,
                    secured=False) \
                .prefetch_related('option_group') \
                .select_related('option_group') \
                .distinct()

            # Combine two or more queryset
            queryset = queryset | queryset_all

            # JSON Api
            serializer = AttributeSerializer(
               queryset, many=True, context=context)

            # Basic profile
            basics = [
                {
                    'value': {
                        'field': 'value_text',
                        'object': user.first_name,
                        'object_print': None,
                        'required': False,
                    },
                    'type': 'text',
                    'identifier': 'first_name',
                    'label': _("Nama Depan"),
                    'option_group': None,
                    'secured': False,
                    'minlength': 3,
                },
                {
                    'value': {
                        'field': 'value_text',
                        'object': user.last_name,
                        'object_print': None,
                        'required': False,
                    },
                    'type': 'text',
                    'identifier': 'last_name',
                    'label': _("Nama Belakang"),
                    'option_group': None,
                    'secured': False,
                    'minlength': 3,
                },
            ]

            response['attributes'] = serializer.data
            response['basics'] = basics
            return Response(response, status=status.HTTP_200_OK)

        # Securities (email, password, username, ect)
        # Restrict for other person
        person = getattr(user, 'person', None)
        if person and securities \
                and identifiers is None and request.user == user:
            telephone_number = None
            values = person.attribute_values
            telephone = values.filter(attribute__identifier='telephone')
            if telephone.exists():
                telephone_number = telephone.first().value

            response = [
                {
                    'value': user.email,
                    'type': 'email',
                    'identifier': 'email',
                    'label': _("Alamat Email"),
                    'secured': True,
                    'minlength': 5,
                },
                {
                    'value': '',
                    'type': 'password',
                    'identifier': 'password',
                    'label': _("Ganti Kata Sandi"),
                    'secured': True,
                    'minlength': 6,
                },
                {
                    'value': user.username,
                    'type': 'text',
                    'identifier': 'username',
                    'label': _("Nama Pengguna"),
                    'secured': True,
                    'minlength': 3,
                },
                {
                    'value': telephone_number,
                    'type': 'number',
                    'identifier': 'telephone',
                    'label': _("Nomor Ponsel"),
                    'secured': True,
                    'minlength': 10,
                }
            ]

            return Response(response, status=status.HTTP_200_OK)
        raise NotAcceptable(detail=_("Data tidak valid."))

    # Update person attributes
    @method_decorator(csrf_protect)
    @transaction.atomic
    def update(self, request, uuid=None):
        """ Update attribute values """
        response = {}
        action = request.data.get('action', None)
        secure_code = request.data.get('secure_code', None)

        if action is None:
            raise NotAcceptable(detail=_("Data tidak valid."))

        if uuid:
            try:
                uuid = UUID(uuid)
                person = Person.objects.get(uuid=uuid)
            except ValueError:
                raise Http404

        # Udate attribute
        if action == 'update_attribute':
            # Update basic profile
            if hasattr(request, 'user') and 'first_name' in request.data or \
                                            'last_name' in request.data:
                user = request.user
                if 'first_name' in request.data:
                    first_name = request.data.pop('first_name')
                    user.first_name = first_name

                if 'last_name' in request.data:
                    last_name = request.data.pop('last_name')
                    user.last_name = last_name
                user.save()

            # Append file
            if request.FILES:
                setattr(request.data, 'files', request.FILES)

            # Remove telehone number
            if 'telephone' in request.data:
                del request.data['telephone']

            # Update attribute
            update_attribute_values(
                person, identifiers=None, values=request.data)
            response['uuid'] = uuid

        # Update basic data (username, password, email, other)
        if action == 'update_basic':
            # This value individually for change
            new_value = request.data.get('new_value', None)
            identifier = request.data.get('identifier', None)
            secured = request.data.get('secured', None)

            # Get user object
            user = request.user

            # Restrict action with validation
            if secured is True and secured is not None:
                if secure_code is None and new_value is None:
                    raise NotAcceptable(detail=_("Data tidak valid."))

                is_passed = validate_secure_code(self, secure_code=secure_code)
                if is_passed is None:
                    raise NotFound()

                # Email
                if identifier == 'email':
                    user.email = new_value

                # Username
                if identifier == 'username':
                    user.username = new_value

                # Password
                if identifier == 'password':
                    user.set_password(new_value)

                # Telephone
                if identifier == 'telephone':
                    param = {'telephone': new_value}
                    update_attribute_values(
                        person,
                        identifiers=['telephone'],
                        values=param)

                # Delete old session
                del self.request.session[secure_code]

            # Non restrict change
            if secured is False and secured is not None:
                pass

            # Save!
            if identifier != 'telephone':
                user.save()
            response['new_value'] = new_value
        return Response(response, status=status.HTTP_200_OK)

    # Sub-action request change options
    @method_decorator(csrf_protect)
    @transaction.atomic
    @action(methods=['post'], detail=False,
            permission_classes=[IsAuthenticated],
            url_path='request-change', url_name='request_change_option')
    def request_change_option(self, request):
        """ Create secure code for change option
        ---------------
        JSON Format:
        {
            "option": "what option will change?",
        } """

        response = {}
        action = request.data.get('action', None)
        secure_code_init = request.data.get('secure_code_init', None)
        value = request.data.get('value', None)
        new_value = request.data.get('new_value', None)
        identifier = request.data.get('identifier', None)

        if action is None:
            raise NotFound()

        user = request.user
        if hasattr(user, 'person'):
            email = user.email

            # If change is email we use new email to send secure code
            if identifier == 'email':
                email = new_value

            sc = send_secure_code(
                self, email=email, action=action,
                secure_code_init=secure_code_init,
                identifier=identifier)

            if sc is not None:
                response['detail'] = _("Periksa email Anda untuk memvalidasi.")
                return Response(response, status=status.HTTP_200_OK)
            raise NotAcceptable(detail=_("Data tidak benar."))
        raise NotFound()

    # Sub-action check option value used or not
    @method_decorator(csrf_protect)
    @transaction.atomic
    @action(methods=['post'], detail=False,
            permission_classes=[IsAuthenticated],
            url_path='change-check', url_name='change_check')
    def change_check(self, request):
        """ Create secure code for change option
        ---------------
        JSON Format:
        {
            "option": "what option will change?",
        } """

        response = {}
        action = request.data.get('action', None)
        new_value = request.data.get('new_value', None)
        identifier = request.data.get('identifier', None)

        if action is None and new_value is None:
            raise NotFound()

        user = request.user
        if hasattr(user, 'person'):
            response['status'] = False

            # Email
            if identifier == 'email':
                if UserModel.objects.filter(email__iexact=new_value).exists():
                    raise NotAcceptable(detail=_('Email validasi berhasil dikirim.'))
                response['new_value'] = new_value
                response['status'] = True
                return Response(response, status=status.HTTP_200_OK)

            # Username
            if identifier == 'username':
                if UserModel.objects.filter(username__iexact=new_value) \
                        .exists():
                    raise NotAcceptable(detail=_('Nama pengguna tidak tersedia.'))
                response['new_value'] = new_value
                response['status'] = True
                return Response(response, status=status.HTTP_200_OK)
            raise NotAcceptable(detail=_("Data tidak benar."))
        raise NotFound()
