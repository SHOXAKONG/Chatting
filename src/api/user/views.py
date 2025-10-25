from django.contrib.auth import logout
from django.utils import timezone
from rest_framework.viewsets import GenericViewSet
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import action
from .serializers import (
    RegisterSerializer,
    ForgotPasswordSerializer,
    RestorePasswordSerializer,
    UserPublicSerializer,
    UserGetSerializer
)

from src.apps.user.models import User, Code
from ...apps.common.task import send_html_email_task


class AuthViewSet(GenericViewSet):
    queryset = User.objects.all()

    def get_serializer_class(self):
        if self.action in ['register']:
            return RegisterSerializer
        elif self.action in ['get_public_user']:
            return UserPublicSerializer
        elif self.action in ['forgot_password']:
            return ForgotPasswordSerializer
        elif self.action in ['restore_password']:
            return RestorePasswordSerializer
        elif self.action in ['public']:
            return UserPublicSerializer
        return UserGetSerializer

    @action(methods=['post'], detail=False, url_path='register')
    def register(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(UserGetSerializer(user).data, status=status.HTTP_201_CREATED)

    @action(methods=['get'], detail=False, url_path='public_user')
    def get_public_user(self, request):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(methods=['get'], detail=True, url_path='public')
    def public(self, request, pk=None):
        user = self.get_object()
        serializer = self.get_serializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(methods=['post'], detail=False, url_path='forgot_password')
    def forgot_password(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        user = User.objects.get(email=email)
        send_html_email_task(user.email, str(user.id))

        return Response({"message": "We sent a code to your email to reset your password."},
                        status=status.HTTP_200_OK)

    @action(methods=['post'], detail=False, url_path='restore_password')
    def restore_password(self, request):
        code = request.data.get('code')
        if not code:
            return Response({"error": "Code is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            code_obj = Code.objects.get(code=code)
        except Code.DoesNotExist:
            return Response({"error": 'Invalid Code.'}, status=status.HTTP_400_BAD_REQUEST)

        if code_obj.expired_time < timezone.now():
            return Response({"error": "Code has expired."}, status=status.HTTP_400_BAD_REQUEST)

        user = code_obj.user
        serializer = self.get_serializer(data=request.data, context={'user': user})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        code_obj.delete()

        return Response({"message": "Password updated successfully."}, status=status.HTTP_200_OK)

    @action(detail=False, methods=["delete"], url_path="logout")
    def logout(self, request):
        logout(request)
        return Response(
            {"message": "Logged out successfully."},
            status=status.HTTP_204_NO_CONTENT
        )
