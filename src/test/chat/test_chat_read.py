import pytest
from ..base import TestBaseClass
from src.apps.chat.models import Chat, Message
from datetime import timedelta
from django.utils import timezone

BASE = "/api/chatting/chats"


@pytest.mark.django_db
class TestChatRead(TestBaseClass):

    def test_read_marks_until_id_from_other_user(self):
        me = self.base_user(email="me@ex.com")
        peer = self.base_user(email="peer@ex.com")
        chat = Chat.objects.create(owner=me, user=peer)

        m1 = Message.objects.create(chat=chat, owner=peer, message="1")
        m2 = Message.objects.create(chat=chat, owner=peer, message="2")
        m3 = Message.objects.create(chat=chat, owner=peer, message="3")
        mine = Message.objects.create(chat=chat, owner=me, message="mine")

        base = timezone.now()
        Message.objects.filter(pk=m1.pk).update(created_at=base + timedelta(microseconds=1))
        Message.objects.filter(pk=m2.pk).update(created_at=base + timedelta(microseconds=2))
        Message.objects.filter(pk=m3.pk).update(created_at=base + timedelta(microseconds=3))
        Message.objects.filter(pk=mine.pk).update(created_at=base + timedelta(microseconds=4))

        m1.refresh_from_db()
        m2.refresh_from_db()
        m3.refresh_from_db()
        mine.refresh_from_db()

        self.authenticate(me)

        res = self.client.post(
            f"{BASE}/{chat.id}/read/",
            data={"message_id": str(m2.id)},
            format="json",
        )
        assert res.status_code == 200, res.content
        assert res.json()["updated"] == 2

        m1.refresh_from_db()
        m2.refresh_from_db()
        m3.refresh_from_db()
        assert (m1.is_read, m2.is_read, m3.is_read) == (True, True, False)

    def test_read_requires_uuid(self):
        me = self.base_user(email="me2@ex.com")
        peer = self.base_user(email="peer2@ex.com")
        chat = Chat.objects.create(owner=me, user=peer)

        self.authenticate(me)

        res = self.client.post(
            f"{BASE}/{chat.id}/read/",
            data={"message_id": "abc"},
            format=self.base_format()
        )
        assert res.status_code == 400
        assert "message_id must be UUID" in res.json()["detail"]

        res2 = self.client.post(
            f"{BASE}/{chat.id}/read/",
            data={"message_id": "00000000-0000-0000-0000-000000000000"},
            format=self.base_format()
        )
        assert res2.status_code == 400
        assert "Message not found" in res2.json()["detail"]
