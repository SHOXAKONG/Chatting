import pytest
from ..base import TestBaseClass
from django.contrib.auth import get_user_model

User = get_user_model()
BASE = "/api/users/auth"

@pytest.mark.django_db
class TestPublicUsers(TestBaseClass):

    def test_get_public_user_list(self):
        # prepare few users
        self.base_user(email="a@ex.com")
        self.base_user(email="b@ex.com")

        client = self.base_client()
        res = client.get(f"{BASE}/public_user/", format=self.base_format())
        assert res.status_code == 200, res.content
        data = res.json()
        assert isinstance(data, list)
        assert len(data) >= 2

    def test_get_public_user_detail(self):
        u = self.base_user(email="public@ex.com")

        client = self.base_client()
        res = client.get(f"{BASE}/{u.id}/public/", format=self.base_format())
        assert res.status_code == 200, res.content
        data = res.json()
        # Depending on your UserPublicSerializer fields:
        assert "id" in data or "email" in data
