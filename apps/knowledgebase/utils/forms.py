from django import forms

# Project UTILS
from utils.validators import get_model

Article = get_model('knowledgebase', 'Article')


class ArticleModelForm(forms.ModelForm):
    uuid_field = forms.UUIDField(required=False)

    class Meta:
        model = Article
        fields = '__all__'
