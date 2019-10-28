import os
import uuid
import calendar
import time

from django.core.exceptions import ObjectDoesNotExist
from django.template.defaultfilters import slugify
from django.core.files.storage import FileSystemStorage


class FileSystemStorageExtend(FileSystemStorage):
    def generate_filename(self, filename, *agrs, **kwargs):
        # Format [timestamp]-[entity]-[object_uuid]-[filename].[ext]
        # Output: 12345675-media-99-mountain.jpg
        dirname, filename = os.path.split(filename)
        file_root, file_ext = os.path.splitext(filename)

        instance = kwargs.get('instance', None)
        content_type = slugify(instance.content_type)
        object_uuid = instance.uuid
        timestamp = calendar.timegm(time.gmtime())

        filename = '{0}_{1}_{2}_{3}'.format(
            timestamp, content_type, object_uuid, file_root)
        return os.path.normpath(
            os.path.join(
                dirname, self.get_valid_name(slugify(filename)+file_ext)))


def object_from_uuid(self, obj=None, *args, **kwargs):
    """Get object from uuid"""
    if obj is None:
        return None

    uuid_init = kwargs.get('uuid_init', None)
    if uuid_init is None:
        return None

    # Validate uuid is valid
    try:
        uuid_init = uuid.UUID(uuid_init)
    except ValueError:
        return None

    # Get object
    try:
        obj = obj.objects.get(uuid=uuid_init)
    except ObjectDoesNotExist:
        return None
    return obj


def find_parent_key(d, value):
    for k, v in d.items():
        if isinstance(v, dict):
            p = find_parent_key(v, value)
            if p:
                return k
        elif v == value:
            return k
    return None


def find_value_with_key(the_key, the_tuple):
    result = None

    if not the_key and not the_tuple:
        return result

    for key, value in the_tuple:
        try:
            value_dict = dict(value)
            result = str(value_dict[int(the_key)])
        except KeyError:
            pass
    return result


def tuple_to_dict(tuple_list):
    result = dict()
    for key, value in tuple_list:
        result.setdefault(key, {}).update(value)
    return result
