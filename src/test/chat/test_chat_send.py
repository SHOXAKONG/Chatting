import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from ..base import TestBaseClass
from src.apps.chat.models import Chat, Message

BASE = "/api/chatting/chats"

@pytest.mark.django_db
class TestChatSend(TestBaseClass):
    def test_send_text_message(self):
        me = self.base_user(email="me@ex.com")
        peer = self.base_user(email="peer@ex.com")
        chat = Chat.objects.create(owner=me, user=peer)

        self.authenticate(me)
        res = self.client.post(
            f"{BASE}/{chat.id}/send/",
            data={"text": "hello"},
            format=self.base_format()
        )
        assert res.status_code == 201, res.content
        data = res.json()
        assert data["message"] == "hello"
        assert Message.objects.filter(chat=chat, owner=me, message="hello").exists()

    def test_send_with_file(self):
        me = self.base_user(email="me2@ex.com")
        peer = self.base_user(email="peer2@ex.com")
        chat = Chat.objects.create(owner=me, user=peer)

        self.authenticate(me)
        file = SimpleUploadedFile("note.txt", b"payload", content_type="text/plain")
        res = self.client.post(
            f"{BASE}/{chat.id}/send/",
            data={"text": "with file", "file": file},
            format="multipart"
        )
        assert res.status_code == 201, res.content
        msg_id = res.json()["id"]
        m = Message.objects.get(pk=msg_id)
        assert m.file
        assert m.file_size == 7
