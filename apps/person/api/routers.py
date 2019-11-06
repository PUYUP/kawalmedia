from django.urls import path, include

# THIRD PARTY
from rest_framework.routers import DefaultRouter

# LOCAL
from .views import (
    TokenObtainPairViewExtend,
    TokenRefreshView,
    SecureActionApiView
)

from .basic.views import PersonApiView
from .attribute.views import AttributeApiView
from .validation.views import ValidationApiView

# Create a router and register our viewsets with it.
router = DefaultRouter()
router.register('persons', PersonApiView, basename='person')
router.register('attributes', AttributeApiView, basename='attribute')
router.register('validations', ValidationApiView, basename='validation')
router.register('secures', SecureActionApiView, basename='secure')

app_name = 'person'

# The API URLs are now determined automatically by the router.
urlpatterns = [
    path('', include((router.urls, 'person'), namespace='persons')),
    path('token/', TokenObtainPairViewExtend.as_view(),
         name='token-obtain-pair'),
    path('token/refresh/', TokenRefreshView.as_view(),
         name='token-refresh'),
]
