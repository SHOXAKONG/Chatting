from rest_framework import serializers
from src.apps.chat.models import Message

class MessageSerializer(serializers.ModelSerializer):
    owner_id = serializers.UUIDField(read_only=True)
    file_url = serializers.SerializerMethodField()
    is_mine  = serializers.SerializerMethodField()
    status   = serializers.SerializerMethodField()

    class Meta:
        model = Message
        fields = (
            "id",
            "owner_id",
            "message",
            "file_url",
            "file_size",
            "is_read",
            "read_at",
            "created_at",
            "is_mine",
            "status",
        )

    def get_file_url(self, obj):
        req = self.context.get("request")
        return req.build_absolute_uri(obj.file.url) if req and obj.file else None

    def get_is_mine(self, obj):
        req = self.context.get("request")
        user = getattr(req, "user", None)
        return bool(user and obj.owner_id == user.id)

    def get_status(self, obj):
        return "read" if obj.is_read else "sent"
