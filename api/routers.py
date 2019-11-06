from django.urls import path, include

from .views import RootApiView

from apps.person.api import routers as person_routers
from apps.escort.api import routers as escort_routers
from apps.knowledgebase.api import routers as knowledgebase_routers
from apps.notice.api import routers as notice_routers

urlpatterns = [
    path('', RootApiView.as_view(), name='api'),
    path('person/', include((person_routers, 'person'), namespace='persons')),
    path('escort/', include((escort_routers, 'escort'), namespace='escorts')),
    path('notice/', include((notice_routers, 'notice'), namespace='notices')),
    path('knowledgebase/', include((knowledgebase_routers, 'knowledgebase'),
                                   namespace='knowledgebases')),
]
