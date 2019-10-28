from django.db import models

from .models_abstract import *

# Project UTILS
from utils.validators import is_model_registered

__all__ = []


# 0
if not is_model_registered('knowledgebase', 'Article'):
    class Article(AbstractArticle):
        class Meta(AbstractArticle.Meta):
            db_table = 'knowledgebase_article'

    __all__.append('Article')


# 1
if not is_model_registered('knowledgebase', 'Attachment'):
    class Attachment(AbstractAttachment):
        class Meta(AbstractAttachment.Meta):
            db_table = 'knowledgebase_attachment'

    __all__.append('Attachment')
