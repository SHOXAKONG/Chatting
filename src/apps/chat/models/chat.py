from src.apps.common.models import BaseModel
from django.db import models
from src.apps.user.models import User


class Chat(BaseModel):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chat_owner')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chat_user')

    class Meta:
        db_table = 'chats'

    def __str__(self):
        return f"{self.owner} - {self.user}"

    def partner_for(self, me_id: int) -> User | None:
        if me_id == self.owner_id:
            return self.user
        if me_id == self.user_id:
            return self.owner
        return None

    def is_participant(self, user_id: int) -> bool:
        return user_id == self.owner_id or user_id == self.user_id
