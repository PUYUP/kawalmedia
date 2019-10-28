import os
import calendar
import time

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