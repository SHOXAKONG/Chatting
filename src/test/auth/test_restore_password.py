import pytest
from datetime import timedelta
from django.utils import timezone
from django.contrib.auth import get_user_model
from ..base import TestBaseClass
from src.apps.user.models import Code

User = get_user_model()
BASE = "/api/users/auth"

@pytest.mark.django_db
class TestRestorePassword(TestBaseClass):

    def test_restore_password_success(self):
        user = self.base_user(email="bar@ex.com")
        code = Code.objects.create(
            user=user,
            code="123456",
            expired_time=timezone.now() + timedelta(minutes=10)
        )

        client = self.base_client()
        payload = {
            "code": "123456",
            "password": "NewP@ssw0rd!",
            "password_confirm": "NewP@ssw0rd!",
        }
        res = client.post(f"{BASE}/restore_password/", data=payload, format=self.base_format())
        assert res.status_code == 200, res.content
        # Code consumed (deleted)
        assert not Code.objects.filter(pk=code.pk).exists()

        user.refresh_from_db()
        assert user.check_password("NewP@ssw0rd!")

    def test_restore_password_missing_code(self):
        client = self.base_client()
        payload = {"password": "A1b2c3d4!", "password_confirm": "A1b2c3d4!"}
        res = client.post(f"{BASE}/restore_password/", data=payload, format=self.base_format())
        assert res.status_code == 400

    def test_restore_password_invalid_code(self):
        client = self.base_client()
        payload = {"code": "000000", "password": "A1b2c3d4!", "password_confirm": "A1b2c3d4!"}
        res = client.post(f"{BASE}/restore_password/", data=payload, format=self.base_format())
        assert res.status_code == 400

    def test_restore_password_expired_code(self):
        user = self.base_user(email="expired@ex.com")
        Code.objects.create(
            user=user,
            code="999999",
            expired_time=timezone.now() - timedelta(minutes=1)
        )
        client = self.base_client()
        payload = {"code": "999999", "password": "A1b2c3d4!", "password_confirm": "A1b2c3d4!"}
        res = client.post(f"{BASE}/restore_password/", data=payload, format=self.base_format())
        assert res.status_code == 400

    def test_restore_password_mismatch(self):
        user = self.base_user(email="mismatch@ex.com")
        Code.objects.create(
            user=user,
            code="111111",
            expired_time=timezone.now() + timedelta(minutes=5)
        )
        client = self.base_client()
        payload = {"code": "111111", "password": "A1b2c3d4!", "password_confirm": "DIFFerent1!"}
        res = client.post(f"{BASE}/restore_password/", data=payload, format=self.base_format())
        assert res.status_code == 400
