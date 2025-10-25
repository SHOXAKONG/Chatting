from django.urls import path, include

urlpatterns = [
    path('users/', include('src.api.user.urls')),
    path('chatting/', include('src.api.chat.urls')),
]
