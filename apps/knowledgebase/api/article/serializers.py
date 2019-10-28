import uuid

from django.conf import settings
from django.db import transaction
from django.utils.translation import ugettext_lazy as _

# THIRD PARTY
from rest_framework import serializers
from rest_framework.response import Response
from rest_framework import status

# PROJECT UTILS
from utils.validators import get_model

# LOCAL UTILS
from ...utils.constant import PUBLISHED

Article = get_model('knowledgebase', 'Article')


class ArticleSerializer(serializers.ModelSerializer):
    """Protest model serializers"""
    url = serializers.HyperlinkedIdentityField(
        view_name='knowledgebases:article-detail', lookup_field='uuid',
        read_only=True)
    writer = serializers.CharField(source='writer.user.username')

    class Meta:
        model = Article
        exclude = ['id']


class SingleArticleSerializer(serializers.ModelSerializer):
    writer = serializers.CharField(source='writer.user.username')

    class Meta:
        model = Article
        exclude = ['id']
