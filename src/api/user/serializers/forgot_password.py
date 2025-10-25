from rest_framework import serializers
from src.apps.user.models import User
from django.utils.translation import gettext_lazy as _


class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField(write_only=True)

    def validate_email(self, value):
        if not User.objects.filter(email=value).exists():
            raise serializers.ValidationError(_('This email is not registered'))
        return value
