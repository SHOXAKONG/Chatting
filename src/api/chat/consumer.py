import json
from django.db.models import Q
from django.utils import timezone
from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer

from src.apps.chat.models import Chat, Message
from src.apps.user.models import User


class ChatConsumer(AsyncWebsocketConsumer):
    @database_sync_to_async
    def _get_chat_by_identifier(self, ident: str):
        try:
            return Chat.objects.get(pk=int(ident))
        except (ValueError, Chat.DoesNotExist):
            pass

        if hasattr(Chat, "uuid"):
            return Chat.objects.filter(uuid=ident).first()
        return None

    @database_sync_to_async
    def _is_participant(self, chat_id: int, user_id: int) -> bool:
        return Chat.objects.filter(
            id=chat_id
        ).filter(
            Q(owner_id=user_id) | Q(user_id=user_id)
        ).exists()

    @database_sync_to_async
    def _create_message(self, chat_id: int, sender_id: int, text: str) -> dict:
        msg = Message.objects.create(
            chat_id=chat_id,
            owner_id=sender_id,
            message=text,
        )
        return {
            "id": msg.id,
            "chat_id": chat_id,
            "sender_id": sender_id,
            "text": msg.message,
            "file_url": msg.file.url if msg.file else None,
            "file_size": msg.file_size,
            "is_read": msg.is_read,
            "read_at": msg.read_at.isoformat() if msg.read_at else None,
            "created_at": msg.created_at.isoformat() if msg.created_at else None,
        }

    @database_sync_to_async
    def _mark_read(self, chat_id: int, message_id: int, reader_id: int) -> bool:
        try:
            msg = Message.objects.get(id=message_id, chat_id=chat_id)
        except Message.DoesNotExist:
            return False

        if msg.owner_id == reader_id:
            return False

        if not msg.is_read:
            msg.is_read = True
            msg.read_at = timezone.now()
            msg.save(update_fields=["is_read", "read_at"])
        return True

    async def connect(self):
        self.user: User = self.scope.get("user")
        if not self.user or not self.user.is_authenticated:
            await self.close(code=4401)  # unauthorized
            return

        self.chat_ident = self.scope["url_route"]["kwargs"]["chat_id"]
        chat = await self._get_chat_by_identifier(self.chat_ident)
        if not chat:
            await self.close(code=4404)
            return

        is_participant = await self._is_participant(chat.id, self.user.id)
        if not is_participant:
            await self.close(code=4403)
            return

        self.chat_id = chat.id
        self.room_group_name = f"chat_{self.chat_id}"

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, "room_group_name"):
            await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data=None, bytes_data=None):
        if not text_data:
            await self.send(json.dumps({"error": "no_payload"}))
            return

        try:
            data = json.loads(text_data)
        except json.JSONDecodeError:
            await self.send(json.dumps({"error": "invalid_json"}))
            return

        action = data.get("action")

        if action == "send_message":
            text = (data.get("text") or "").strip()
            if not text:
                await self.send(json.dumps({"error": "empty_text"}))
                return

            payload = await self._create_message(self.chat_id, self.user.id, text)
            await self.channel_layer.group_send(
                self.room_group_name,
                {"type": "chat_message", "message": payload},
            )

        elif action == "read":
            message_id = data.get("message_id")
            if not isinstance(message_id, int):
                await self.send(json.dumps({"error": "invalid_message_id"}))
                return

            ok = await self._mark_read(self.chat_id, message_id, self.user.id)
            if ok:
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        "type": "notification",
                        "notification": {"kind": "read", "message_id": message_id, "by": self.user.id},
                    },
                )
            else:
                await self.send(json.dumps({"error": "cannot_mark_read"}))

        else:
            await self.send(json.dumps({"error": "unknown_action"}))

    async def chat_message(self, event):
        await self.send(text_data=json.dumps(event["message"]))

    async def notification(self, event):
        await self.send(text_data=json.dumps(event["notification"]))
