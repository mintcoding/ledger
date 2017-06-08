from django.core.exceptions import ImproperlyConfigured
from ledger.settings_base import *

ROOT_URLCONF = 'disturbance.urls'
SITE_ID = 1

INSTALLED_APPS += [
    'bootstrap3',
    'disturbance',
    'disturbance.components.main',
    'disturbance.components.organisations',
    'disturbance.components.users',
    'disturbance.components.proposals',
    'taggit',
    'rest_framework',
    'rest_framework_gis'
]

SITE_ID = 1

# maximum number of days allowed for a booking
WSGI_APPLICATION = 'disturbance.wsgi.application'

'''REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': (
        'disturbance.perms.OfficerPermission',
    )
}'''

MIDDLEWARE_CLASSES += [
    'disturbance.middleware.FirstTimeNagScreenMiddleware'
]

TEMPLATES[0]['DIRS'].append(os.path.join(BASE_DIR, 'disturbance', 'templates'))
TEMPLATES[0]['DIRS'].append(os.path.join(BASE_DIR, 'disturbance','components','organisations', 'templates'))
TEMPLATES[0]['DIRS'].append(os.path.join(BASE_DIR, 'disturbance','components','emails', 'templates'))
BOOTSTRAP3 = {
    'jquery_url': '//static.dpaw.wa.gov.au/static/libs/jquery/2.2.1/jquery.min.js',
    'base_url': '//static.dpaw.wa.gov.au/static/libs/twitter-bootstrap/3.3.6/',
    'css_url': None,
    'theme_url': None,
    'javascript_url': None,
    'javascript_in_head': False,
    'include_jquery': False,
    'required_css_class': 'required-form-field',
    'set_placeholder': False,
}
STATICFILES_DIRS.append(os.path.join(os.path.join(BASE_DIR, 'disturbance', 'static')))
DEV_STATIC = env('DEV_STATIC',False)
DEV_STATIC_URL = env('DEV_STATIC_URL')
if DEV_STATIC and not DEV_STATIC_URL:
    raise ImproperlyConfigured('If running in DEV_STATIC, DEV_STATIC_URL has to be set')
DATA_UPLOAD_MAX_NUMBER_FIELDS = None 
