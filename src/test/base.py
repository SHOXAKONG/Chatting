import uuid

from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from src.apps.user.models import User


class TestBaseClass:
    def base_client(self):
        return APIClient()

    def base_format(self):
        return 'json'

    def base_user(self, email=None):
        email = email or f'test_{uuid.uuid4().hex[:6]}@info.com'
        return User.objects.create_user(email=email, password='password123')

    def refresh_token(self):
        self.refresh = RefreshToken.for_user(self.base_user())
        return str(self.refresh)

    def authenticate(self, user):
        self.refresh = RefreshToken.for_user(user)
        self.access_token = str(self.refresh.access_token)
        self.client = self.base_client()
        return self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")
