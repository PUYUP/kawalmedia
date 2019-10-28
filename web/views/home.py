import random
import string
import uuid
import datetime

from django.views import View
from django.shortcuts import render
from django.db import IntegrityError
from django.db.models import Count, F, Value
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.sessions.backends.db import SessionStore
from django.http import JsonResponse

from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes

from utils.validators import get_model
from apps.person.utils.auths import (
    account_verification_token,
    get_person_uuid,
    get_user,
    create_secure_code,
    validate_secure_code
)

User = get_model('auth', 'User')
Person = get_model('person', 'Person')
Role = get_model('person', 'Role')
Attribute = get_model('person', 'Attribute')
AttributeValue = get_model('person', 'AttributeValue')


class HomeView(View):
    template_name = 'web/home.html'
    context = {}

    def get(self, request):
        print(datetime.timedelta(hours=32))
        return render(request, self.template_name, self.context)

    def post(self, request):
        response = {
            'abc': 'xyz'
        }

        if request.is_ajax():
            response['ajax'] = True
            request.session['zzz'] = 'bla'
            request.session.create()
        return JsonResponse(response)
