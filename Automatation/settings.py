"""
Django settings for Automatation project.

Generated by 'django-admin startproject' using Django 4.2.1.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.2/ref/settings/
"""

from pathlib import Path
import os
# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-=ut$#i*am-b5@gw!qm204o)b*%rs3h10@qs_*5y2ev^fqp6m(y'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# ALLOWED_HOSTS = ['localhost','127.0.0.1']
ALLOWED_HOSTS = ['*']


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'corsheaders',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.facebook',
    'allauth.socialaccount.providers.instagram',
    'allauth.socialaccount.providers.google',
    'sslserver',

    'allauth.socialaccount.providers.linkedin_oauth2',
    "django_extensions",
    'rest_framework',
    'django_htmx',

    # 'allauth.socialaccount.providers.linkedin_oauth2',
    'app'
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    "corsheaders.middleware.CorsMiddleware",
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django_htmx.middleware.HtmxMiddleware',

]
CORS_ALLOW_ALL_ORIGINS = True

# CSRF_TRUSTED_ORIGINS=['https://c681-72-255-15-110.ngrok-free.app']
# CORS_URLS_REGEX = r'^/accounts/register/.*$'

LOGIN_REDIRECT_URL = "dashboard"
LOGOUT_REDIRECT_URL = "base"


ROOT_URLCONF = 'Automatation.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': ['app/templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]
AUTHENTICATION_BACKENDS = [
    # ...
    # Needed to login by username in Django admin, regardless of `allauth`
    # 'django.contrib.auth.backends.ModelBackend',

    # `allauth` specific authentication methods, such as login by e-mail
    'allauth.account.auth_backends.AuthenticationBackend',
    # 'allauth.socialaccount.providers.facebook.FacebookOAuth2Provider',
    # ...
]

WSGI_APPLICATION = 'Automatation.wsgi.application'


# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

SOCIALACCOUNT_ADAPTER = 'app.linkedin_adapter.MyAdapter'
SOCIALACCOUNT_STORE_TOKENS=True

# Provider specific settings
SOCIALACCOUNT_PROVIDERS = {
    'facebook': {
        # For each OAuth based provider, either add a ``SocialApp``
        # (``socialaccount`` app) containing the required client
        # credentials, or list them here:
    'SCOPE': [
            'read_insights',
            'catalog_management',
            'publish_video',
            'private_computation_access',
            'user_managed_groups',
            'groups_show_list',
            'pages_manage_cta',
            'pages_manage_instant_articles',
            'pages_show_list',
            'read_page_mailboxes',
            'business_management',
            'pages_messaging',
            'pages_messaging_phone_number',
            'pages_messaging_subscriptions',
            'instagram_basic',
            'instagram_manage_comments',
            'instagram_manage_insights',
            'instagram_content_publish',
            'publish_to_groups',
            'groups_access_member_info',
            'leads_retrieval',
            'instagram_manage_messages',
            'attribution_read',
            'page_events',
            'pages_read_engagement',
            'pages_manage_metadata',
            'pages_read_user_content',
            'pages_manage_ads',
            'pages_manage_posts',
            'pages_manage_engagement',
            ],
        'APP': {
            'client_id': '3154199121547431',
            'secret': 'c567975277f2b79c0e59adb09e2ee1b8',
            'key': ''
        }
    },
    'instagram': {
        # For each OAuth based provider, either add a ``SocialApp``
        # (``socialaccount`` app) containing the required client
        # credentials, or list them here:
        'APP': {
            'client_id': '183679611336967',
            'secret': 'bdebb21b9ffb7712de43b6612ffa5920',

            'key': ''
        },
        # 'redirect_uri': 'https://6c5b-2407-aa80-15-84dc-3576-ad96-daa1-e897.ngrok-free.app/redirect_uri/',
        'SCOPE': ['user_profile', 'user_email'],
    },
    'google': {
        # For each OAuth based provider, either add a ``SocialApp``
        # (``socialaccount`` app) containing the required client
        # credentials, or list them here:
        'APP': {
            'client_id': '33836610262-gvtpcrjpbdefm0td6e0g7e4c76gut9s8.apps.googleusercontent.com',
            'secret': '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',
            'key': ''
        },

        'SCOPE': [
                'profile',
                'email',
                'https://www.googleapis.com/auth/business.manage'
            ],
        'AUTH_PARAMS': {
                'access_type': 'online',
            },
        'OAUTH_PKCE_ENABLED': True,

        },

    'linkedin_oauth2': {

        # For each OAuth based provider, either add a ``SocialApp``
        # (``socialaccount`` app) containing the required client
        # credentials, or list them here:
        'SCOPE': [
                    'r_emailaddress',
                    'r_liteprofile',
                    'openid',
                    'r_ads_reporting',
                    'r_organization_social',
                    'rw_organization_admin',
                    'w_member_social',
                    'r_ads',
                    'r_emailaddress',
                    'w_organization_social',
                    'rw_ads',
                    'r_basicprofile',
                    'r_organization_admin',
                    'email',
                    'r_1st_connections_size',
        ],
        'APP': {

            'client_id': '78brbn2ezf10mr',
            'secret': '71JKMVxT5SQAh9i6',
            'key': '',

        },

    },
}
DATABASES = {
    'default': {

        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'smart_pre',
        'USER': 'smart_pre',
        'PASSWORD': 'smart123!',
        'HOST': 'localhost',
        'PORT': '5432',

    }
}
AUTH_USER_MODEL = 'app.user'


#
# # Celery Configuration
# CELERY_BROKER_URL = 'redis://127.0.0.1:6379/0'
# CELERY_RESULT_BACKEND = 'redis://127.0.0.1:6379/0'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
# CELERY_TIMEZONE = 'Asia/Karachi'


SOCIALACCOUNT_STORE_TOKENS = True

SITE_ID = 1

# Internationalization
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Asia/Karachi'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static')
STATICFILES_DIR = [
        os.path.join(BASE_DIR, 'static')
]

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
EMAIL_HOST = "localhost"
EMAIL_PORT = 1025
if DEBUG:
    SSL_CERTIFICATE = '/Users/apple/PycharmProjects/WebAutomation/Automatation/certificate.crt'
    SSL_KEY = '/Users/apple/PycharmProjects/WebAutomation/Automatation/private.key'

    # Optional: Set the SSL/TLS port (default is 8443)
    SSL_PORT = 443

    # Optional: Set the SSL/TLS host (default is 'localhost')
    SSL_HOST = 'localhost'

    # Set the SSL/TLS certificate paths
    # SSLCERT = '/Users/apple/PycharmProjects/WebAutomation/Automatation/certificate.crt'
    # SSLKEY = '/Users/apple/PycharmProjects/WebAutomation/Automatation/private.key'
    #
    # # Configure the SSL/TLS server
    # SSLSERVER_CERT = SSLCERT
    # SSLSERVER_KEY = SSLKEY
    SSL_SERVER_REDIRECT_HTTPS = True



# CORS_ORIGIN_WHITELIST = [
#     'https://6c5b-2407-aa80-15-84dc-3576-ad96-daa1-e897.ngrok-free.app',
#     # Other allowed origins if needed
# ]

GRAPH_MODELS = {
  'all_applications': True,
  'group_models': True,
}

CORS_ALLOW_ALL_ORIGINS = True
SOCIALACCOUNT_ADAPTER  = 'app.adapter.CustomAccountAdapter'
