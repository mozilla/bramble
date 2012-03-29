# This is your project's main settings file that can be committed to your
# repo. If you need to override a setting locally, use settings_local.py

from funfactory.settings_base import *

# Bundles is a dictionary of two dictionaries, css and js, which list css files
# and js files that can be bundled together by the minify app.
MINIFY_BUNDLES = {
    'css': {
        'common_css': (
            'css/common/main.css',
            'css/bootstrap/bootstrap.css',
            'css/bootstrap/bootstrap-responsive.css',
        ),
    },
    'js': {
        'common_js': (
            'js/common/libs/jquery-1.7.2.min.js',
            'js/common/libs/jquery.ba-resize.js',
            'js/common/libs/jquery.flot.js',
            'js/common/libs/jquery.flot.stack.js',
            'js/common/libs/jquery.flot.resize.js',
            'js/common/charts.js',
        ),
    }
}

# Defines the views served for root URLs.
ROOT_URLCONF = 'bramble.urls'

INSTALLED_APPS = list(INSTALLED_APPS) + [
    # Application base, containing global templates.
    'bramble.base',

]


# Because Jinja2 is the default template loader, add any non-Jinja templated
# apps here:
JINGO_EXCLUDE_APPS = [
    'admin',
]

MIDDLEWARE_EXCLUDE_CLASSES = [
    'funfactory.middleware.LocaleURLMiddleware',
]

MIDDLEWARE_CLASSES = list(MIDDLEWARE_CLASSES)

for app in MIDDLEWARE_EXCLUDE_CLASSES:
    if app in MIDDLEWARE_CLASSES:
        MIDDLEWARE_CLASSES.remove(app)

MIDDLEWARE_CLASSES = tuple(MIDDLEWARE_CLASSES)

## No DB necessary

DATABASES = {}

## Log settings

SYSLOG_TAG = "http_app_bramble"

LOGGING = dict(loggers=dict(bramble={'level': logging.DEBUG}))

# Common Event Format logging parameters
CEF_PRODUCT = 'Bramble'
CEF_VENDOR = 'Mozilla'


## Caching

CACHES = {
    'default': {
        'BACKEND': 'redis_cache.RedisCache',
        'LOCATION': 'localhost:6379',
        'OPTIONS': {
            'DB': 3,
            #'PASSWORD': 'yadayada',
            #'PARSER_CLASS': 'redis.connection.HiredisParser'
        },
    },
}


## Slaves API
SLAVES_API_URL = 'http://slavealloc.build.mozilla.org/api/slaves'
