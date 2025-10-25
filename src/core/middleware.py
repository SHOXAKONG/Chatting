import jwt
from src.core import settings
from urllib.parse import parse_qs
from django.contrib.auth.models import AnonymousUser
from src.apps.user.models import User
from channels.db import database_sync_to_async


@database_sync_to_async
def get_user(user_id):
    try:
        return User.objects.get(id=user_id)
    except User.DoesNotExist:
        return AnonymousUser()


def JWTAuthMiddleware(inner):
    async def middleware(scope, receive, send):
        query_string = scope.get("query_string", b"").decode()
        token = parse_qs(query_string).get("token", [None])[0]

        if token:
            try:
                payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
                user_id = payload.get("user_id")
                scope["user"] = await get_user(user_id)
            except jwt.InvalidTokenError:
                scope["user"] = AnonymousUser()
        else:
            scope["user"] = AnonymousUser()

        return await inner(scope, receive, send)

    return middleware