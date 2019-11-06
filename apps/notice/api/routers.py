from django.urls import path, include

# THIRD PARTY
from rest_framework.routers import DefaultRouter

# LOAD API VIEW
from .notification.views import NotificationApiView

# Create a router and register our viewsets with it.
router = DefaultRouter()
router.register('notifications', NotificationApiView, basename='notification')

app_name = 'notice'

# The API URLs are now determined automatically by the router.
urlpatterns = [
    path('', include((router.urls, 'notice'), namespace='notices')),
]
