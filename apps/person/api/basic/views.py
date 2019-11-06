from uuid import UUID

from django.db.models import F, Subquery, OuterRef
from django.db import transaction
from django.utils.translation import ugettext_lazy as _
from django.utils.decorators import method_decorator
from django.core.exceptions import ObjectDoesNotExist
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie
from django.views.decorators.cache import never_cache
from django.contrib.sessions.backends.db import SessionStore
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core import exceptions

# THIRD PARTY
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.parsers import (
    FormParser, FileUploadParser, MultiPartParser)
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import (
    NotFound, NotAcceptable, ValidationError)
from rest_framework.pagination import PageNumberPagination

# SERIALIZERS
from .serializers import (
    PersonSerializer, SinglePersonSerializer,
    UpdatePersonSerializer, CreatePersonSerializer)

# PERMISSIONS
from ..permissions import IsOwnerOrReject

# GET MODELS FROM GLOBAL UTILS
from utils.validators import get_model

# LOCAL UTILS
from ...utils.auths import (
    send_secure_code,
    validate_secure_code,
    get_user_from_email,
    get_person_from_secure_code)

Person = get_model('person', 'Person')
UserModel = get_user_model()

# Define to avoid used ...().paginate__
PAGINATOR = PageNumberPagination()


@method_decorator(ensure_csrf_cookie, name='dispatch')
class PersonApiView(viewsets.ViewSet):
    lookup_field = 'uuid'
    permission_classes = (AllowAny,)
    parser_class = (FormParser, FileUploadParser, MultiPartParser,)
    permission_action = {
        # Disable update if not owner
        'retrieve': [IsOwnerOrReject, IsAuthenticated],
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
        """Fetches objects"""
        if uuid and type(uuid) is not UUID:
            try:
                uuid = UUID(uuid)
            except ValueError:
                raise NotFound()

        # Single object
        if uuid:
            try:
                return Person.objects \
                    .prefetch_related('user', 'options', 'roles') \
                    .select_related('user') \
                    .get(uuid=uuid)
            except ValueError:
                raise NotFound()

        # All objects
        return Person.objects.prefetch_related('user') \
            .select_related('user') \
            .all()

    # Return a response
    def get_response(self, serializer, serializer_parent=None):
        """ Output to endpoint """
        response = dict()
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
    @method_decorator(csrf_protect)
    @method_decorator(never_cache)
    @transaction.atomic
    def retrieve(self, request, uuid=None, format=None):
        """ View as single object """
        context = {'request': self.request}
        queryset = self.get_object(uuid=uuid)
        serializer = SinglePersonSerializer(
            queryset, many=False, context=context)
        return Response(serializer.data, status=status.HTTP_200_OK)

    # Register user as person
    @method_decorator(csrf_protect)
    @method_decorator(never_cache)
    @transaction.atomic
    def create(self, request, format=None):
        """ Create single object """
        context = {'request': self.request}
        serializer = CreatePersonSerializer(data=request.data, context=context)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # Update basic user data
    # Email, username, password, ect
    @method_decorator(csrf_protect)
    @method_decorator(never_cache)
    @transaction.atomic
    def partial_update(self, request, uuid=None, format=None):
        """ Update basic info """
        context = {'request': self.request}

        if uuid and type(uuid) is not UUID:
            try:
                uuid = UUID(uuid)
            except ValueError:
                raise NotFound()

        # Single object
        if uuid:
            try:
                instance = UserModel.objects.get(person__uuid=uuid)
            except ObjectDoesNotExist:
                raise NotFound()

        serializer = UpdatePersonSerializer(
            instance, data=request.data, partial=True, context=context)

        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # Sub-action check value used or not
    @method_decorator(csrf_protect)
    @transaction.atomic
    @action(methods=['post'], detail=False,
            permission_classes=[IsAuthenticated],
            url_path='duplicate-check', url_name='duplicate_check')
    def duplicate_check(self, request):
        """
        JSON Format:
        {
            "option": "what option will change?",
        } """

        response = dict()
        new_value = request.data.get('new_value', None)
        identifier = request.data.get('identifier', None)
        person = getattr(request.user, 'person', None)

        if person and identifier and new_value:
            # Email
            if identifier == 'email':
                if UserModel.objects.filter(email__iexact=new_value).exists():
                    raise NotAcceptable(detail=_('Email sudah digunakan.'))
                response['new_value'] = new_value
                return Response(response, status=status.HTTP_200_OK)

            # Username
            if identifier == 'username':
                if UserModel.objects.filter(username__iexact=new_value).exists():
                    raise NotAcceptable(detail=_('Nama pengguna sudah digunakan.'))
                response['new_value'] = new_value
                return Response(response, status=status.HTTP_200_OK)
            raise NotAcceptable(detail=_("Data tidak benar."))
        raise NotFound()

    # Sub-action check value used or not
    @method_decorator(csrf_protect)
    @method_decorator(never_cache)
    @transaction.atomic
    @action(methods=['post'], detail=False,
            permission_classes=[IsAuthenticated],
            url_path='password-check', url_name='password_check')
    def password_check(self, request):
        password = request.data.get('password', None)
        if password:
            errors = dict()

            try:
                # validate the password and catch the exception
                validate_password(password=password, user=request.user)
            except exceptions.ValidationError as e:
                errors['password'] = list(e.messages)

            if errors:
                raise ValidationError(errors)
            return Response(status=status.HTTP_200_OK)
        raise NotFound()

    # Sub-action request password reset
    @method_decorator(csrf_protect)
    @method_decorator(never_cache)
    @transaction.atomic
    @action(methods=['post'], detail=False, permission_classes=[AllowAny],
            url_path='password-request', url_name='password_request')
    def password_request(self, request):
        """
        JSON Format:
        {
            "email": "my@email.com"
        }
        """
        response = dict()
        email = request.data.get('email', None)

        # First request use email
        # And secure_code is none
        if not email:
            raise NotFound(detail=_("Alamat email wajib."))

        user = get_user_from_email(self, email)
        secure_data = send_secure_code(self, email=email, user=user, method=1)

        if secure_data:
            response['detail'] = _("Periksa email Anda ikuti instruksi lebih lanjut.")
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

        response = dict()
        errors = dict()
        secure_code = self.request.data.get('secure_code', None)
        password1 = self.request.data.get('password1', None)
        password2 = self.request.data.get('password2', None)
        is_passed = validate_secure_code(
            self, secure_code=secure_code, is_password_request=True)

        # Make sure session exist!
        if secure_code is not None:
            if password1 and password2:
                if password1 != password2:
                    raise NotAcceptable(
                        detail=_("Kata sandi tidak sama."),
                        code='password_mismatch',
                    )

            # validate the password and catch the exception
            try:
                validate_password(password=password2, user=request.user)
            except exceptions.ValidationError as e:
                errors['password'] = list(e.messages)

            if errors:
                raise ValidationError(errors)

            if is_passed and password1 and password2:
                person = get_person_from_secure_code(self, secure_code=secure_code)
                if hasattr(person, 'user'):
                    user = person.user
                    user.set_password(password2)
                    user.save()
                    response = {'detail': _("Kata sandi berhasil dirubah.")}

                    # Now delete secure code session
                    del self.request.session[secure_code]
                    return Response(response, status=status.HTTP_200_OK)
            raise NotAcceptable({'detail': _("Kode otentikasi salah.")})
        raise NotFound()

    # Sub-action logout
    @method_decorator(csrf_protect)
    @method_decorator(never_cache)
    @transaction.atomic
    @action(methods=['post'], detail=False,
            permission_classes=[IsAuthenticated],
            url_path='logout', url_name='perfom_logout')
    def perfom_logout(self, request):
        # Get saved session by verification code
        response = dict()
        auth_code = self.request.data.get('auth_code', None)
        session_key = self.request.session.session_key

        if auth_code or session_key:
            # del self.request.session[auth_code]
            s = SessionStore(session_key=session_key)
            s.delete()
        return Response(status=status.HTTP_200_OK)
