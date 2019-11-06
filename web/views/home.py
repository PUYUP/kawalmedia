import random
import string
import uuid
import datetime

from django.views import View
from django.shortcuts import render
from django.db import IntegrityError
from django.db.models import Count, Q, F, Value
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.sessions.backends.db import SessionStore
from django.http import JsonResponse
from django.contrib.contenttypes.models import ContentType

from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes

# PROJECT UTILS
from utils.validators import get_model


class HomeView(View):
    template_name = 'web/home.html'
    context = dict()

    def get(self, request):
        return render(request, self.template_name, self.context)
