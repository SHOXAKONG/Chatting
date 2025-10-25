import pytest
from django.urls import reverse
from ..base import TestBaseClass

BASE = "/api/users/auth"

@pytest.mark.django_db
class TestForgotPassword(TestBaseClass):
    def test_forgot_password_ok(self, mocker):
        user = self.base_user(email="foo@ex.com")

        mocked = mocker.patch("src.api.user.views.send_html_email_task", autospec=True)

        res = self.base_client().post(
            f"{BASE}/forgot_password/",
            data={"email": user.email},
            format=self.base_format(),
        )
        assert res.status_code == 200, res.content

        assert mocked.called
        args, kwargs = mocked.call_args

        flat = list(args) + list(kwargs.values())
        flat_str = {str(x) for x in flat}

        assert user.email in flat or user.email in flat_str
        assert str(user.id) in flat_str
