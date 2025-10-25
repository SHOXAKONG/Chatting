from rest_framework.routers import DefaultRouter
from .views import ChatViewSet
from django.urls import path, include

router = DefaultRouter()
router.register('chats', ChatViewSet, basename='chat')
urlpatterns = [
    path('', include(router.urls))
]
