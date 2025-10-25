import uuid

import pytest
from ..base import TestBaseClass
from src.apps.chat.models import Chat

BASE = "/api/chatting/chats"

@pytest.mark.django_db
class TestChatListRetrieve(TestBaseClass):
    def test_list_requires_auth(self):
        client = self.base_client()
        res = client.get(f"{BASE}/", format=self.base_format())
        assert res.status_code in (401, 403)

    def test_list_only_my_chats(self):
        me = self.base_user(email="me@ex.com")
        other = self.base_user(email="other@ex.com")

        Chat.objects.create(owner=me, user=other)  # mine
        stranger1 = self.base_user(email="s1@ex.com")
        stranger2 = self.base_user(email="s2@ex.com")
        Chat.objects.create(owner=stranger1, user=stranger2)  # not mine

        self.authenticate(me)
        res = self.client.get(f"{BASE}/", format=self.base_format())
        assert res.status_code == 200
        data = res.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert uuid.UUID(data[0]["partner"]["id"]) == other.id

    def test_retrieve_my_chat(self):
        me = self.base_user(email="me@ex.com")
        peer = self.base_user(email="peer@ex.com")
        chat = Chat.objects.create(owner=me, user=peer)

        self.authenticate(me)
        res = self.client.get(f"{BASE}/{chat.id}/", format=self.base_format())
        assert res.status_code == 200
        assert uuid.UUID(res.json()["id"]) == chat.id
