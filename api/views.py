from django.views import View

# THIRD PARTY
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.permissions import AllowAny


class RootApiView(APIView):
    permission_classes = (AllowAny,)

    def get(self, request, format=None):
        return Response({
            'user': {
                'persons': reverse('persons:person:person-list', request=request,
                                   format=format, current_app='person'),
                'attributes': reverse('persons:person:attribute-list', request=request,
                                      format=format, current_app='person'),
                'validations': reverse('persons:person:validation-list', request=request,
                                       format=format, current_app='person'),
            },
            'escort': {
                'medias': reverse('escorts:escort:media-list', request=request,
                                  format=format, current_app='escort'),
                'ratings': reverse('escorts:escort:rating-list', request=request,
                                   format=format, current_app='escort'),
                'attributes': reverse('escorts:escort:attribute-list', request=request,
                                      format=format, current_app='escort'),
                'protests': reverse('escorts:escort:protest-list', request=request,
                                    format=format, current_app='escort'),
                'attachments': reverse('escorts:escort:attachment-list', request=request,
                                       format=format, current_app='escort'),
                'thumbs': reverse('escorts:escort:thumb-list', request=request,
                                  format=format, current_app='escort'),
                'comments': reverse('escorts:escort:comment-list', request=request,
                                    format=format, current_app='escort'),
            },
            'notice': {
                'notifications': reverse('notices:notice:notification-list', request=request,
                                         format=format, current_app='notice'),
            },
            'knowledgebase': {
                'articles': reverse('knowledgebases:knowledgebase:article-list', request=request,
                                    format=format, current_app='knowledgebase'),
                'attachments': reverse('knowledgebases:knowledgebase:attachment-list', request=request,
                                       format=format, current_app='knowledgebase'),
            },
        })
