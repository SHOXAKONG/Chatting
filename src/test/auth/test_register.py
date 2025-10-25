import uuid
import pytest
from django.contrib.auth import get_user_model
from ..base import TestBaseClass

User = get_user_model()
BASE = "/api/users/auth"


@pytest.mark.django_db
class TestRegister(TestBaseClass):

    def test_register_success(self):
        client = self.base_client()
        payload = {
            "email": f"user_{uuid.uuid4().hex[:6]}@ex.com",
            "password": "P@ssw0rd123!",
            "password_confirm": "P@ssw0rd123!",
            "first_name": "Foo",
            "last_name": "Bar",
        }
        res = client.post(f"{BASE}/register/", data=payload, format=self.base_format())
        assert res.status_code == 201, res.content
        data = res.json()
        assert data["email"] == payload["email"]
        assert User.objects.filter(email=payload["email"]).exists()

    def test_register_missing_password(self):
        client = self.base_client()
        email = f"user_{uuid.uuid4().hex[:6]}@ex.com"
        res = client.post(f"{BASE}/register/", data={"email": email}, format=self.base_format())
        assert res.status_code in (400, 422)
