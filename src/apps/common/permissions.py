from rest_framework import permissions

class IsParticipant(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return getattr(obj, 'owner_id', None) == request.user.id or getattr(obj, 'user_id', None) == request.user.id