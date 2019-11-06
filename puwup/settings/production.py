from .base import *
from .staging import *

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '5-953x)k!)u6u(_i0e^p0d_1i6%sk8@lr0z_vh@=_&tm++a5l4'

DEBUG = False
ALLOWED_HOSTS = ['kawal-media-aws-db.clautt90drah.us-east-2.rds.amazonaws.com']

# Database
# https://docs.djangoproject.com/en/2.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'kawal-media-aws-db',
        'USER': 'admin',
        'PASSWORD': '(z4ZGwNPyf3DiUumwf',
        'HOST': 'kawal-media-aws-db.clautt90drah.us-east-2.rds.amazonaws.com',  # Or an IP Address that your DB is hosted on
        'PORT': '3306',
        'OPTIONS': {
            'sql_mode': 'STRICT_TRANS_TABLES',
        }
    }
}
