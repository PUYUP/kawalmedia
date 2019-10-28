from django.urls import path, include

from .views.home import HomeView

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
]
