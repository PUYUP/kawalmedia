from django.urls import path, include

# THIRD PARTY
from rest_framework.routers import DefaultRouter

# LOAD API VIEW
from .media.views import MediaApiView
from .rating.views import RatingApiView
from .attribute.views import AttributeApiView, ConstantApiView
from .protest.views import ProtestApiView
from .attachment.views import AttachmentApiView
from .thumbed.views import ThumbedApiView
from .comment.views import CommentApiView

# Create a router and register our viewsets with it.
router = DefaultRouter()
router.register('medias', MediaApiView, basename='media')
router.register('ratings', RatingApiView, basename='rating')
router.register('attributes', AttributeApiView, basename='attribute')
router.register('protests', ProtestApiView, basename='protest')
router.register('attachments', AttachmentApiView, basename='attachment')
router.register('thumbs', ThumbedApiView, basename='thumb')
router.register('comments', CommentApiView, basename='comment')
router.register('constants', ConstantApiView, basename='constant')

app_name = 'escort'

# The API URLs are now determined automatically by the router.
urlpatterns = [
    path('', include((router.urls, 'escort'), namespace='escorts')),
]
