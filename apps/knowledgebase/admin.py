from django.contrib import admin

# Project UTILS
from utils.validators import get_model

# Local UTILS
from .utils.forms import ArticleModelForm

Person = get_model('person', 'Person')
Article = get_model('knowledgebase', 'Article')
Attachment = get_model('knowledgebase', 'Attachment')


class ArticleAdmin(admin.ModelAdmin):
    """Extend Article admin"""
    model = Article
    list_display = ('label', 'status', 'writer', 'date_updated',)
    form = ArticleModelForm

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'writer':
            kwargs['queryset'] = Person.objects.prefetch_related('user') \
                .select_related('user')
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.prefetch_related('writer') \
            .select_related('writer')

    def get_form(self, request, obj=None, *args, **kwargs):
        if obj:
            self.form.base_fields['uuid_field'].initial = obj.uuid

        return super().get_form(request, *args, **kwargs)

    class Media:
        js = ('admin/ckeditor/ckeditor.js', 'admin/ckeditor/ckeditor-config.js',)


admin.site.register(Article, ArticleAdmin)
admin.site.register(Attachment)
