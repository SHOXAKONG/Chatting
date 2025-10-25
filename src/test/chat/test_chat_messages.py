import pytest
from django.utils import timezone
from datetime import timedelta
from ..base import TestBaseClass
from src.apps.chat.models import Chat, Message

BASE = "/api/chatting/chats"

@pytest.mark.django_db
class TestChatMessages(TestBaseClass):
    def _seed_msgs(self, chat, a, b):
        m1 = Message.objects.create(chat=chat, owner=a, message="first")
        m2 = Message.objects.create(chat=chat, owner=b, message="second")
        m3 = Message.objects.create(chat=chat, owner=a, message="third")
        t0 = timezone.now() - timedelta(minutes=3)
        Message.objects.filter(pk=m1.pk).update(created_at=t0)
        Message.objects.filter(pk=m2.pk).update(created_at=t0 + timedelta(minutes=1))
        Message.objects.filter(pk=m3.pk).update(created_at=t0 + timedelta(minutes=2))
        m1.refresh_from_db(); m2.refresh_from_db(); m3.refresh_from_db()
        return m1, m2, m3

    def test_messages_default_asc(self):
        a = self.base_user(email="a@ex.com")
        b = self.base_user(email="b@ex.com")
        chat = Chat.objects.create(owner=a, user=b)
        m1, m2, m3 = self._seed_msgs(chat, a, b)

        self.authenticate(a)
        res = self.client.get(f"{BASE}/{chat.id}/messages/", format=self.base_format())
        assert res.status_code == 200
        ids = [x["id"] for x in res.json()]
        assert ids == [m1.id, m2.id, m3.id]

    def test_messages_desc(self):
        a = self.base_user(email="a2@ex.com")
        b = self.base_user(email="b2@ex.com")
        chat = Chat.objects.create(owner=a, user=b)
        m1, m2, m3 = self._seed_msgs(chat, a, b)

        self.authenticate(a)
        res = self.client.get(f"{BASE}/{chat.id}/messages/?order=desc", format=self.base_format())
        assert res.status_code == 200
        ids = [x["id"] for x in res.json()]
        assert ids == [m3.id, m2.id, m1.id]
