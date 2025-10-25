import pytest
from ..base import TestBaseClass

BASE = "/api/users/auth"

@pytest.mark.django_db
class TestLogout(TestBaseClass):

    def test_logout_unauthenticated_is_204(self):
        client = self.base_client()
        res = client.delete(f"{BASE}/logout/", format=self.base_format())
        assert res.status_code == 204

    def test_logout_authenticated_is_204(self):
        user = self.base_user(email="logout@ex.com")
        client = self.base_client()
        self.client = client
        self.authenticate(user)
        res = client.delete(f"{BASE}/logout/", format=self.base_format())
        assert res.status_code == 204
