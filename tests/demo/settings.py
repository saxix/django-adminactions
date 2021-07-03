import os

here = os.path.dirname(__file__)
# sys.path.append(os.path.abspath(os.path.join(here, os.pardir)))
# sys.path.append(os.path.abspath(os.path.join(here, os.pardir, 'demo')))

DEBUG = True
TEMPLATE_DEBUG = DEBUG

db = os.environ.get('DBENGINE', None)
if db == 'pg':
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql_psycopg2',
            'NAME': 'adminactions',
            'HOST': os.environ.get('PG_HOST', '127.0.0.1'),
            'PORT': os.environ.get('PG_PORT', ''),
            'USER': os.environ.get('PG_USER', 'postgres'),
            'PASSWORD': os.environ.get('PG_PASSWORD', ''),
            }}
elif db == 'mysql':
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': 'adminactions',
            'HOST': os.environ.get('MYSQL_HOST', '127.0.0.1'),
            'PORT': os.environ.get('MYSQL_PORT', ''),
            'USER': os.environ.get('MYSQL_USER', 'root'),
            'PASSWORD': os.environ.get('MYSQL_PASSWORD', ''),

            'CHARSET': 'utf8',
            'COLLATION': 'utf8_general_ci',
            'TEST': {
                'CHARSET': 'utf8',
                'COLLATION': 'utf8_general_ci',
            },
            'TEST_CHARSET': 'utf8',
            'TEST_COLLATION': 'utf8_general_ci'}}
elif db == 'myisam':
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': 'adminactions',
            'HOST': os.environ.get('MYSQL_HOST', '127.0.0.1'),
            'PORT': os.environ.get('MYSQL_PORT', ''),
            'USER': os.environ.get('MYSQL_USER', 'root'),
            'PASSWORD': os.environ.get('MYSQL_PASSWORD', ''),

            'CHARSET': 'utf8',
            'OPTIONS': {'init_command': 'SET storage_engine=MyISAM'},
            'COLLATION': 'utf8_general_ci',
            'TEST': {
                'CHARSET': 'utf8',
                'COLLATION': 'utf8_general_ci',
            },
            'TEST_CHARSET': 'utf8',
            'TEST_COLLATION': 'utf8_general_ci'}}
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': 'adminactions.sqlite',
            'TEST': {
                'NAME': ':memory:',
            },
            'TEST_NAME': ':memory:',
            'HOST': '',
            'PORT': '',
            'ATOMIC_REQUESTS': True}}

TIME_ZONE = 'Asia/Bangkok'
LANGUAGE_CODE = 'en-us'
SITE_ID = 1
USE_I18N = True
USE_L10N = True
USE_TZ = True
MEDIA_ROOT = os.path.join(here, 'media')
MEDIA_URL = ''
STATIC_ROOT = os.path.join(here, 'static')
STATIC_URL = '/static/'
SECRET_KEY = 'c73*n!y=)tziu^2)y*@5i2^)$8z$tx#b9*_r3i6o1ohxo%*2^a'

MIDDLEWARE = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',)

MESSAGE_STORAGE = 'demo.storage.PlainCookieStorage'

ROOT_URLCONF = 'demo.urls'


from adminactions.perms import AA_PERMISSION_CREATE_USE_COMMAND

AA_PERMISSION_HANDLER = AA_PERMISSION_CREATE_USE_COMMAND

INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.admin',
    'admin_extra_urls',
    'adminactions.apps.Config',
    'demo']

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
        'LOCATION': 'unique-snowflake'
    }
}

ENABLE_SELENIUM = True

DATE_FORMAT = 'd-m-Y'
TIME_FORMAT = 'H:i'
DATETIME_FORMAT = 'd-m-Y H:i'
YEAR_MONTH_FORMAT = 'F Y'
MONTH_DAY_FORMAT = 'F j'
SHORT_DATE_FORMAT = 'm/d/Y'
SHORT_DATETIME_FORMAT = 'm/d/Y P'
FIRST_DAY_OF_WEEK = 1

# CSRF_COOKIE_DOMAIN = 'localhost'
CSRF_COOKIE_HTTPONLY = False
CSRF_COOKIE_NAME = 'csrftoken'
CSRF_COOKIE_PATH = '/'
CSRF_COOKIE_SECURE = False
CSRF_HEADER_NAME = 'HTTP_X_CSRFTOKEN'
# CSRF_TRUSTED_ORIGINS = ['localhost']

# Django 1.9

TEMPLATES = [
    {'BACKEND': 'django.template.backends.django.DjangoTemplates',
     'DIRS': [],
     'APP_DIRS': True,
     'OPTIONS': {
         'debug': DEBUG,
         'context_processors': [
             'django.contrib.auth.context_processors.auth',
             'django.template.context_processors.debug',
             'django.template.context_processors.i18n',
             'django.template.context_processors.media',
             'django.template.context_processors.static',
             'django.template.context_processors.tz',
             "django.template.context_processors.request",
             'django.contrib.messages.context_processors.messages',
         ],
     },
     }
]
AUTH_PASSWORD_VALIDATORS = [
    # {
    # 'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    # },
    # {
    #     'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    # },
    # {
    #     'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    # },
    # {
    #     'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    # },
]
