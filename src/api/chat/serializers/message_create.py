from rest_framework import serializers


class MessageCreateSerializer(serializers.Serializer):
    text = serializers.CharField(required=False, allow_blank=False)
    file = serializers.FileField(required=False)

    def validate(self, attrs):
        if not attrs.get('text') and not attrs.get('file'):
            raise serializers.ValidationError("Provide 'text' or 'file'.")
        return attrs
