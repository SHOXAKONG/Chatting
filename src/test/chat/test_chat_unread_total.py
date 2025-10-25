import pytest
from ..base import TestBaseClass
from src.apps.chat.models import Chat, Message

BASE = "/api/chatting/chats"

@pytest.mark.django_db
class TestChatUnreadTotal(TestBaseClass):
    def test_unread_total_counts_only_from_others(self):
        me = self.base_user(email="me@ex.com")
        peer = self.base_user(email="peer@ex.com")
        chat = Chat.objects.create(owner=me, user=peer)

        Message.objects.create(chat=chat, owner=peer, message="u1")
        Message.objects.create(chat=chat, owner=peer, message="u2")
        Message.objects.create(chat=chat, owner=me, message="mine")
        Message.objects.create(chat=chat, owner=peer, message="read", is_read=True)

        self.authenticate(me)
        res = self.client.get(f"{BASE}/unread_total/", format=self.base_format())
        assert res.status_code == 200
        assert res.json()["total"] == 2
