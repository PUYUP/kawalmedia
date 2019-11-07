from .base import *
from .staging import *

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '5-953x)k!)u6u(_i0e^p0d_1i6%sk8@lr0z_vh@=_&tm++a5l4'

DEBUG = False
ALLOWED_HOSTS = ['127.0.0.1', 'localhost', 'puyup-app.appspot.com',
                 'puyup-app.firebaseapp.com']

# Database
# https://docs.djangoproject.com/en/2.2/ref/settings/#databases

# [START db_setup]
if os.getenv('GAE_APPLICATION', None):
    # Running on production App Engine, so connect to Google Cloud SQL using
    # the unix socket at /cloudsql/<your-cloudsql-connection string>
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'HOST': '/cloudsql/puyup-app:asia-southeast1:kawal-media',
            'USER': 'kawal-media-db-user',
            'PASSWORD': '(z4ZGwNPyf3DiUumwf',
            'NAME': 'kawal_media_db',
        }
    }
else:
    # Running locally so connect to either a local MySQL instance or connect
    # to Cloud SQL via the proxy.  To start the proxy via command line:
    #    $ cloud_sql_proxy -instances=[INSTANCE_CONNECTION_NAME]=tcp:3306
    # See https://cloud.google.com/sql/docs/mysql-connect-proxy
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'HOST': '127.0.0.1',
            'PORT': '3306',
            'USER': 'kawal-media-db-user',
            'PASSWORD': '(z4ZGwNPyf3DiUumwf',
            'NAME': 'kawal_media_db',
        }
    }
# [END db_setup]
