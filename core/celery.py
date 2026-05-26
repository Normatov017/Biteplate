import os

from celery import Celery


os.environ.setdefault(

    'DJANGO_SETTINGS_MODULE',

    'core.settings'

)


app = Celery('core')


# =========================
# REDIS CONFIG
# =========================

app.conf.broker_url = (
    'redis://127.0.0.1:6379/0'
)

app.conf.result_backend = (
    'redis://127.0.0.1:6379/0'
)


# =========================
# LOAD SETTINGS
# =========================

app.config_from_object(

    'django.conf:settings',

    namespace='CELERY'

)


# =========================
# AUTO DISCOVER
# =========================

app.autodiscover_tasks()