from uuid import UUID
import string

HEX = set(string.hexdigits)
from django.db import transaction
from django.db.models import Q, OuterRef, Subquery
from django.utils import timezone

from rest_framework import mixins, viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response

from src.apps.chat.models import Chat, Message
from .serializers import (
    ChatSerializer, MessageSerializer, MessageCreateSerializer
)
from src.apps.common.permissions import IsParticipant
from src.apps.user.models import User


def get_or_create_chat_between(u1_id, u2_id) -> Chat:
    u1 = UUID(str(u1_id))
    u2 = UUID(str(u2_id))

    if u1 == u2:
        raise ValueError("Cannot chat with yourself")
    a, b = sorted([u1, u2], key=lambda x: x.int)
    chat = Chat.objects.filter(owner_id=a, user_id=b).first()
    if chat:
        return chat
    return Chat.objects.create(owner_id=a, user_id=b)


def _is_canonical_uuid(s: str) -> bool:
    if not isinstance(s, str) or len(s) != 36:
        return False
    if s[8] != "-" or s[13] != "-" or s[18] != "-" or s[23] != "-":
        return False
    return all((c in HEX) or (c == "-") for c in s)


class ChatViewSet(mixins.ListModelMixin,
                  mixins.RetrieveModelMixin,
                  viewsets.GenericViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ChatSerializer

    def get_queryset(self):
        me = self.request.user
        queryset = Chat.objects.filter(Q(owner_id=me.id) | Q(user_id=me.id))

        last_msg_qs = Message.objects.filter(chat_id=OuterRef('pk')).order_by('-created_at')
        queryset = queryset.annotate(
            _last_msg_at=Subquery(last_msg_qs.values('created_at')[:1]),
        ).order_by('-_last_msg_at', '-updated_at').select_related('owner', 'user')

        return queryset

    def get_object(self):
        obj = Chat.objects.select_related('owner', 'user').get(pk=self.kwargs['pk'])
        self.check_object_permissions(self.request, obj)
        return obj

    @action(detail=False, methods=['POST'])
    def open(self, request):
        peer_raw = request.data.get('user_id')
        if not peer_raw:
            return Response({'detail': 'user_id is required'}, status=400)

        try:
            peer_uuid = UUID(str(peer_raw))
        except Exception:
            return Response({'detail': 'user_id is invalid'}, status=400)

        if peer_uuid == request.user.id:
            return Response({'detail': 'Cannot chat with yourself'}, status=400)

        try:
            User.objects.get(id=peer_uuid, is_active=True)
        except User.DoesNotExist:
            return Response({'detail': 'User not found'}, status=404)

        chat = get_or_create_chat_between(request.user.id, peer_uuid)
        Chat.objects.filter(id=chat.id).update(updated_at=timezone.now())
        return Response(ChatSerializer(chat, context={'request': request}).data)

    @action(detail=True, methods=['GET'], permission_classes=[permissions.IsAuthenticated, IsParticipant])
    def messages(self, request, pk=None):
        chat = self.get_object()
        order = request.query_params.get('order', 'asc')
        ordering = 'created_at' if order != 'desc' else '-created_at'
        queryset = chat.messages.select_related('owner').order_by(ordering, 'id')
        page = self.paginate_queryset(queryset)
        serializer = MessageSerializer(page or queryset, many=True, context={'request': request})
        if page is not None:
            return self.get_paginated_response(serializer.data)
        return Response(serializer.data)

    @action(detail=True, methods=['POST'], permission_classes=[permissions.IsAuthenticated, IsParticipant])
    def send(self, request, pk=None):
        chat = self.get_object()

        file_obj = request.FILES.get('file')
        data = request.data.copy()
        if file_obj:
            data['file'] = file_obj

        text = (data.get('text') or '').strip()

        if not text and not file_obj:
            return Response({"detail": "text or file is required"}, status=status.HTTP_400_BAD_REQUEST)

        ser = MessageCreateSerializer(data=data, context={'request': request})
        ser.is_valid(raise_exception=True)

        file_validated = ser.validated_data.get('file')
        with transaction.atomic():
            msg = Message.objects.create(
                chat=chat,
                owner=request.user,
                message=ser.validated_data.get('text', ''),
                file=file_validated,
                file_size=(file_validated.size if file_validated else None),
            )
            Chat.objects.filter(id=chat.id).update(updated_at=timezone.now())

        return Response(MessageSerializer(msg, context={'request': request}).data, status=status.HTTP_201_CREATED)

    @action(methods=["post"], detail=True, permission_classes=[permissions.IsAuthenticated, IsParticipant])
    def read(self, request, pk=None):
        chat = self.get_object()

        me_id = request.user.id
        other_id = chat.user_id if chat.owner_id == me_id else chat.owner_id

        msg_raw = request.data.get("message_id")
        if msg_raw is None:
            return Response({"detail": "message_id is required"}, status=status.HTTP_400_BAD_REQUEST)

        msg_id = str(msg_raw)
        if not _is_canonical_uuid(msg_id):
            return Response({"detail": "message_id must be UUID"}, status=status.HTTP_400_BAD_REQUEST)

        target_msg = (
            Message.objects
            .filter(id=msg_id, chat_id=chat.id)
            .only("id", "created_at")
            .first()
        )
        if not target_msg:
            return Response({"detail": "Message not found"}, status=status.HTTP_400_BAD_REQUEST)

        field_names = {f.name for f in Message._meta.get_fields()}
        has_created_at = "created_at" in field_names

        with transaction.atomic():
            qs = Message.objects.filter(chat_id=chat.id, owner_id=other_id, is_read=False)
            if has_created_at:
                qs = qs.filter(created_at__lte=target_msg.created_at)
            if not has_created_at:  # fallback without else
                qs = qs.filter(id__lte=target_msg.id)

            updated = qs.update(is_read=True, read_at=timezone.now())

        return Response({"updated": updated}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['GET'])
    def unread_total(self, request):
        me = request.user.id
        total = Message.objects.filter(chat__in=self.get_queryset()) \
            .exclude(owner_id=me) \
            .filter(is_read=False).count()
        return Response({'total': total})

    @action(detail=False, methods=['GET'])
    def search(self, request):
        q = (request.query_params.get('q') or '').strip()
        if not q:
            return Response([], status=200)

        me_id = request.user.id
        chats = self.get_queryset()

        partner_chat_ids = chats.filter(
            (Q(owner__first_name__icontains=q) & ~Q(owner_id=me_id)) |
            (Q(user__first_name__icontains=q) & ~Q(user_id=me_id))
        ).values_list('id', flat=True)

        msg_chat_ids = (
            Message.objects
            .filter(chat_id__in=chats.values('id'), message__icontains=q)
            .values_list('chat_id', flat=True)
            .distinct()
        )

        result_ids = set(partner_chat_ids) | set(msg_chat_ids)
        result_qs = chats.filter(id__in=result_ids)
        data = ChatSerializer(result_qs, many=True, context={'request': request}).data
        return Response(data, status=200)
