from django.urls import path, include

# THIRD PARTY
from rest_framework.routers import DefaultRouter

# LOAD API VIEW
from .article.views import ArticleApiView
from .attachment.views import AttachmentApiView

# Create a router and register our viewsets with it.
router = DefaultRouter()
router.register('articles', ArticleApiView, basename='article')
router.register('attachments', AttachmentApiView, basename='attachment')

app_name = 'knowledgebase'

# The API URLs are now determined automatically by the router.
urlpatterns = [
    path('', include((router.urls, 'knowledgebase'), namespace='knowledgebases')),
]
