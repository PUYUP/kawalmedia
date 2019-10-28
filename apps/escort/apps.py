from django.apps import AppConfig
from django.db.models.signals import post_save, post_delete, post_init


class EscortConfig(AppConfig):
    name = 'apps.escort'

    def ready(self):
        from apps.escort.signals import (
            media_handler,
            rating_handler,
            rating_delete_handler,
            protest_init_handler,
            protest_handler,
            protest_delete_handler,
            attribute_handler,
            thumbed_handler,
            thumbed_delete_handler,
            comment_handler,
            comment_delete_handler)
        from utils.validators import get_model

        # Create media signal
        try:
            Media = get_model('escort', 'Media')
        except LookupError:
            Media = None

        if Media:
            post_save.connect(
                media_handler, sender=Media, dispatch_uid='media_signal')

        # Create rating signal
        try:
            Rating = get_model('escort', 'Rating')
        except LookupError:
            Rating = None

        if Rating:
            post_save.connect(
                rating_handler, sender=Rating, dispatch_uid='rating_signal')

            post_delete.connect(
                rating_delete_handler, sender=Rating,
                dispatch_uid='rating_delete_signal')

        # Create protest signal
        try:
            Protest = get_model('escort', 'Protest')
        except LookupError:
            Protest = None

        if Protest:
            post_init.connect(
                protest_init_handler, sender=Protest, dispatch_uid='protest_init_signal')

            post_save.connect(
                protest_handler, sender=Protest, dispatch_uid='protest_signal')

            post_delete.connect(
                protest_delete_handler, sender=Protest,
                dispatch_uid='protest_delete_signal')

        # Create entity attribute
        try:
            Attribute = get_model('escort', 'Attribute')
        except LookupError:
            Attribute = None

        if Attribute:
            post_save.connect(
                attribute_handler, sender=Attribute,
                dispatch_uid='attribute_signal')

        # Create Thumbed signal
        try:
            Thumbed = get_model('escort', 'Thumbed')
        except LookupError:
            Thumbed = None

        if Thumbed:
            post_save.connect(
                thumbed_handler, sender=Thumbed, dispatch_uid='thumbed_signal')

            post_delete.connect(
                thumbed_delete_handler, sender=Thumbed,
                dispatch_uid='thumbed_delete_signal')

        # Create Comment signal
        try:
            Comment = get_model('escort', 'Comment')
        except LookupError:
            Comment = None

        if Comment:
            post_save.connect(
                comment_handler, sender=Comment, dispatch_uid='comment_signal')

            post_delete.connect(
                comment_delete_handler, sender=Comment,
                dispatch_uid='comment_delete_signal')
