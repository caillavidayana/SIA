"""Base aislada para pruebas PostgreSQL; nunca utiliza la base del sistema."""
from .settings_tests import *

DATABASES = {'default': {
    'ENGINE': 'django.db.backends.postgresql',
    'NAME': 'sia_reglas_test_base',
    'USER': 'sia_test',
    'HOST': '127.0.0.1',
    'PORT': os.environ.get('SIA_TEST_POSTGRES_PORT', '55432'),
}}
