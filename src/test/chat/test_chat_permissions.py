import pytest
from ..base import TestBaseClass
from src.apps.chat.models import Chat

BASE = "/api/chatting/chats"

@pytest.mark.django_db
class TestChatPermissions(TestBaseClass):
    def test_messages_forbidden_for_non_participant(self):
        me = self.base_user(email="me@ex.com")
        a = self.base_user(email="a@ex.com")
        b = self.base_user(email="b@ex.com")
        chat = Chat.objects.create(owner=a, user=b)

        self.authenticate(me)
        res = self.client.get(f"{BASE}/{chat.id}/messages/", format=self.base_format())
        assert res.status_code == 403

    def test_send_forbidden_for_non_participant(self):
        me = self.base_user(email="me@ex.com")
        a = self.base_user(email="a@ex.com")
        b = self.base_user(email="b@ex.com")
        chat = Chat.objects.create(owner=a, user=b)

        self.authenticate(me)
        res = self.client.post(f"{BASE}/{chat.id}/send/", data={"text": "hey"}, format=self.base_format())
        assert res.status_code == 403

    def test_read_forbidden_for_non_participant(self):
        me = self.base_user(email="me@ex.com")
        a = self.base_user(email="a@ex.com")
        b = self.base_user(email="b@ex.com")
        chat = Chat.objects.create(owner=a, user=b)

        self.authenticate(me)
        res = self.client.post(f"{BASE}/{chat.id}/read/", data={"message_id": 1}, format=self.base_format())
        assert res.status_code == 403
