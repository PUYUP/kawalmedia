from django.contrib import admin
from django.db.models import (
    Q, F, OuterRef, Subquery, Case, When, CharField)

# Project UTILS
from utils.validators import get_model

Notification = get_model('notice', 'Notification')
NotificationActor = get_model('notice', 'NotificationActor')
NotificationRecipient = get_model('notice', 'NotificationRecipient')
Person = get_model('person', 'Person')
Comment = get_model('escort', 'Comment')
Protest = get_model('escort', 'Protest')


class NotificationAdmin(admin.ModelAdmin):
    """Extend NotificationAdmin"""
    model = Notification
    list_display = ('get_actor', 'verb', 'get_recipient', 'get_content',)

    def get_queryset(self, request):
        comment = Comment.objects.filter(pk=OuterRef('content_id'))
        protest = Protest.objects.filter(pk=OuterRef('content_id'))

        qs = super().get_queryset(request)
        return qs.prefetch_related('content_type', 'content_notified_type',
                                   'content_parent_type', 'content_source_type') \
            .select_related('content_type', 'content_notified_type',
                            'content_parent_type', 'content_source_type') \
            .annotate(
                actor=F('notify_actor_object__actor__user__username'),
                recipient=F('notify_recipient_object__recipient__user__username'),
                content=Case(
                    When(
                        Q(content_type__model='comment'),
                        then=Subquery(comment.values('description')[:1])
                    ),
                    When(
                        Q(content_type__model='protest'),
                        then=Subquery(protest.values('label')[:1])
                    ),
                    default=None,
                    output_field=CharField()
                )
            )

    def get_actor(self, obj):
        return obj.actor

    def get_recipient(self, obj):
        return obj.recipient

    def get_content(self, obj):
        return obj.content

    def save_model(self, request, obj, form, change):
        # Append request to signals
        setattr(obj, 'request', request)
        super().save_model(request, obj, form, change)


class NotificationActorAdmin(admin.ModelAdmin):
    """Extend NotificationActor"""
    model = NotificationActor
    list_display = ('actor', 'get_content',)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'actor':
            kwargs['queryset'] = Person.objects.prefetch_related('user') \
                .select_related('user')

        if db_field.name == 'notification':
            comment = Comment.objects.filter(pk=OuterRef('content_id'))
            protest = Protest.objects.filter(pk=OuterRef('content_id'))

            kwargs['queryset'] = Notification.objects.prefetch_related('content_type') \
                .select_related('content_type') \
                .annotate(
                    actor=F('notify_actor_object__actor__user__username'),
                    recipient=F('notify_recipient_object__recipient__user__username'),
                    content=Case(
                        When(
                            Q(content_type__model='comment'),
                            then=Subquery(comment.values('description')[:1])
                        ),
                        When(
                            Q(content_type__model='protest'),
                            then=Subquery(protest.values('label')[:1])
                        ),
                        default=None,
                        output_field=CharField()
                    )
                )

        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def get_queryset(self, request):
        comment = Comment.objects.filter(pk=OuterRef('notification__content_id'))
        protest = Protest.objects.filter(pk=OuterRef('notification__content_id'))

        qs = super().get_queryset(request)
        return qs.prefetch_related('actor', 'actor__user', 'notification', 'notification__content_type') \
            .select_related('actor', 'actor__user', 'notification', 'notification__content_type') \
            .annotate(
                content=Case(
                    When(
                        Q(notification__content_type__model='comment'),
                        then=Subquery(comment.values('description')[:1])
                    ),
                    When(
                        Q(notification__content_type__model='protest'),
                        then=Subquery(protest.values('label')[:1])
                    ),
                    default=None,
                    output_field=CharField()
                )
            )

    def get_content(self, obj):
        if obj.content:
            return obj.content
        return None

    def save_model(self, request, obj, form, change):
        # Append request to signals
        setattr(obj, 'request', request)
        super().save_model(request, obj, form, change)


class NotificationRecipientAdmin(admin.ModelAdmin):
    """Extend NotificationRecipient"""
    model = NotificationRecipient
    list_display = ('recipient', 'get_content',)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'recipient':
            kwargs['queryset'] = Person.objects.prefetch_related('user') \
                .select_related('user')

        if db_field.name == 'notification':
            comment = Comment.objects.filter(pk=OuterRef('content_id'))
            protest = Protest.objects.filter(pk=OuterRef('content_id'))

            kwargs['queryset'] = Notification.objects.prefetch_related('content_type') \
                .select_related('content_type') \
                .annotate(
                    actor=F('notify_actor_object__actor__user__username'),
                    recipient=F('notify_recipient_object__recipient__user__username'),
                    content=Case(
                        When(
                            Q(content_type__model='comment'),
                            then=Subquery(comment.values('description')[:1])
                        ),
                        When(
                            Q(content_type__model='protest'),
                            then=Subquery(protest.values('label')[:1])
                        ),
                        default=None,
                        output_field=CharField()
                    )
                )

        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def get_queryset(self, request):
        comment = Comment.objects.filter(pk=OuterRef('notification__content_id'))
        protest = Protest.objects.filter(pk=OuterRef('notification__content_id'))

        qs = super().get_queryset(request)
        return qs.prefetch_related('recipient', 'recipient__user', 'notification', 'notification__content_type') \
            .select_related('recipient', 'recipient__user', 'notification', 'notification__content_type') \
            .annotate(
                content=Case(
                    When(
                        Q(notification__content_type__model='comment'),
                        then=Subquery(comment.values('description')[:1])
                    ),
                    When(
                        Q(notification__content_type__model='protest'),
                        then=Subquery(protest.values('label')[:1])
                    ),
                    default=None,
                    output_field=CharField()
                )
            )

    def get_content(self, obj):
        if obj.content:
            return obj.content
        return None

    def save_model(self, request, obj, form, change):
        # Append request to signals
        setattr(obj, 'request', request)
        super().save_model(request, obj, form, change)


# Register your models here.
admin.site.register(Notification, NotificationAdmin)
admin.site.register(NotificationActor, NotificationActorAdmin)
admin.site.register(NotificationRecipient, NotificationRecipientAdmin)
