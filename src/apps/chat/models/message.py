from django.db import models
from .chat import Chat
from src.apps.common.models import BaseModel
from src.apps.user.models import User
from django_minio_backend import MinioBackend, iso_date_prefix


class Message(BaseModel):
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE, related_name='messages')
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='message_owner', null=True)
    message = models.TextField(null=True, blank=True)

    file = models.FileField(storage=MinioBackend(bucket_name="chatting"), upload_to=iso_date_prefix, null=True, blank=True)
    file_size = models.FloatField(null=True, blank=True)

    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'messages'

    def __str__(self):
        return f"{self.chat}"
