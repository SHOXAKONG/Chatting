import uuid

import pytest
from django.utils import timezone
from ..base import TestBaseClass
from src.apps.chat.models import Chat

BASE = "/api/chatting/chats"

@pytest.mark.django_db
class TestChatOpen(TestBaseClass):
    def test_open_requires_valid_user_id(self):
        me = self.base_user(email="me@ex.com")
        self.authenticate(me)
        res = self.client.post(f"{BASE}/open/", data={"user_id": "abc"}, format=self.base_format())
        assert res.status_code == 400
        assert "invalid" in res.json().get("detail", "")

    def test_open_user_not_found(self):
        me = self.base_user(email="me@ex.com")
        self.authenticate(me)

        non_existing_uuid = str(uuid.uuid4())
        res = self.client.post(
            f"{BASE}/open/",
            data={"user_id": non_existing_uuid},
            format=self.base_format()
        )
        assert res.status_code == 404
        assert "User not found" in res.json().get("detail", "")

    def test_open_success_create_then_reopen_returns_same_chat(self):
        me = self.base_user(email="me@ex.com")
        peer = self.base_user(email="peer@ex.com")
        self.authenticate(me)

        r1 = self.client.post(f"{BASE}/open/", data={"user_id": peer.id}, format=self.base_format())
        assert r1.status_code == 200, r1.content
        chat_id = r1.json()["id"]

        r2 = self.client.post(f"{BASE}/open/", data={"user_id": peer.id}, format=self.base_format())
        assert r2.status_code == 200
        assert r2.json()["id"] == chat_id

        chat = Chat.objects.get(pk=chat_id)
        assert chat.updated_at <= timezone.now()

    @pytest.mark.xfail(reason="Current view raises ValueError for self-chat; add a 400 guard to pass this test")
    def test_open_self_chat_returns_400(self):
        me = self.base_user(email="me2@ex.com")
        self.authenticate(me)
        res = self.client.post(f"{BASE}/open/", data={"user_id": me.id}, format=self.base_format())
        assert res.status_code == 400
