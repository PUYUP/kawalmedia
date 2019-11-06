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
    send_secure_code,
    validate_secure_code,
    get_person_from_secure_code,
    get_user_from_uuid,
    get_user_from_email
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


class SecureActionApiView(viewsets.ViewSet):
    permission_classes = (AllowAny,)

    @method_decorator(csrf_protect)
    @method_decorator(never_cache)
    @transaction.atomic
    def create(self, request, format=None):
        """
        {
            "action": "request_secure_code",
            "email": "hellopuyup@gmail.com"
        }

        {
            "action": "validate_secure_code",
            "secure_code": "KMF9E6EA"
        }
        """
        action = request.data.get('action', None)
        method = request.data.get('method', None)
        email = request.data.get('email', None)
        new_value = request.data.get('new_value', None)
        identifier = request.data.get('identifier', None)

        # For secure code validation
        secure_code = request.data.get('secure_code', None)

        # Get user from default user email if logged in
        if self.request.user.is_authenticated:
            user = self.request.user
            email = getattr(user, 'email', None)
        else:
            user = get_user_from_email(self, email)

        # Use new email
        if identifier == 'email':
            email = new_value

        if not action:
            raise NotAcceptable()

        if action == 'request_secure_code':
            secure_data = send_secure_code(
                self, email=email, user=user, new_value=new_value,
                method=method)
            if secure_data:
                return Response(status=status.HTTP_200_OK)
            raise NotFound(detail=_("Email tidak ditemukan."))

        if action == 'validate_secure_code' and secure_code:
            validate = validate_secure_code(self, secure_code=secure_code)
            if validate:
                return Response(status=status.HTTP_200_OK)
            raise NotFound(detail=_("Kode otentikasi salah."))

        raise NotAcceptable()
