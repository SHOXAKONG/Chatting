from rest_framework import serializers
from src.api.user.serializers.user_public import UserPublicSerializer
from src.apps.chat.models import Chat

class ChatSerializer(serializers.ModelSerializer):
    owner = UserPublicSerializer(read_only=True)
    user = UserPublicSerializer(read_only=True)

    partner = serializers.SerializerMethodField()
    last_message_text = serializers.SerializerMethodField()
    last_message_at = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()

    class Meta:
        model = Chat
        fields = (
            "id",
            "owner",
            "user",
            "partner",
            "last_message_text",
            "last_message_at",
            "unread_count",
        )

    def get_partner(self, obj):
        me = self.context["request"].user
        return UserPublicSerializer(obj.partner_for(me.id), context=self.context).data

    def get_last_message_text(self, obj):
        txt = getattr(obj, "_last_msg_text", None)
        has_file = getattr(obj, "_last_msg_has_file", None)
        if txt is not None or has_file is not None:
            return txt or ("📎 Attachment" if has_file else "")
        last = obj.messages.order_by("-created_at").only("message", "file").first()
        return last.message if last and last.message else ("📎 Attachment" if last and last.file else "")

    def get_last_message_at(self, obj):
        ts = getattr(obj, "_last_msg_at", None)
        if ts is not None:
            return ts
        last = obj.messages.order_by("-created_at").only("created_at").first()
        return last.created_at if last else obj.created_at

    def get_unread_count(self, obj):
        cnt = getattr(obj, "_unread_count", None)
        if cnt is not None:
            return cnt
        me = self.context["request"].user
        return obj.messages.filter(is_read=False).exclude(owner_id=me.id).count()
