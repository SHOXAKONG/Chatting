from src.apps.common.models import BaseModel
from django.db import models
from django.contrib.auth.models import AbstractUser
from .manager import UserManager

class User(AbstractUser, BaseModel):
    email = models.EmailField(unique=True, db_index=True)
    username = models.CharField(max_length=200, null=True, blank=True)
    objects = UserManager()
    age = models.IntegerField(default=19)
    first_name = models.CharField(max_length=200, db_index=True)

    REQUIRED_FIELDS = []
    USERNAME_FIELD = 'email'

    def __str__(self):
        return self.email
