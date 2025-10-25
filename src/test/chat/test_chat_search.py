import pytest
from ..base import TestBaseClass
from src.apps.chat.models import Chat, Message

BASE = "/api/chatting/chats"

@pytest.mark.django_db
class TestChatSearch(TestBaseClass):
    def test_search_by_partner_first_name(self):
        me = self.base_user(email="me@ex.com")
        partner = self.base_user(email="alice@ex.com")
        partner.first_name = "Alice"
        partner.save()

        chat = Chat.objects.create(owner=me, user=partner)

        self.authenticate(me)
        res = self.client.get(f"{BASE}/search/?q=Ali", format=self.base_format())
        assert res.status_code == 200
        data = res.json()
        assert isinstance(data, list)
        assert any(c["id"] == str(chat.id) for c in data)

    def test_search_by_message_content(self):
        me = self.base_user(email="me2@ex.com")
        partner = self.base_user(email="bob@ex.com")
        chat = Chat.objects.create(owner=me, user=partner)
        Message.objects.create(chat=chat, owner=partner, message="hello world")

        self.authenticate(me)
        res = self.client.get(f"{BASE}/search/?q=world", format=self.base_format())
        assert res.status_code == 200

        ids = {c["id"] for c in res.json()}
        assert str(chat.id) in ids

    def test_search_empty_query_returns_empty_list(self):
        me = self.base_user(email="me3@ex.com")
        self.authenticate(me)
        res = self.client.get(f"{BASE}/search/?q=", format=self.base_format())
        assert res.status_code == 200
        assert res.json() == []
