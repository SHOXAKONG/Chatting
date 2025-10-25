from .settings import *

DEBUG = True

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

CACHES = {"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}
DEFAULT_FILE_STORAGE = "django.core.files.storage.FileSystemStorage"

import tempfile, pathlib
_tmp = pathlib.Path(tempfile.gettempdir()) / "django_test_media"
_tmp.mkdir(exist_ok=True, parents=True)
MEDIA_ROOT = str(_tmp)
