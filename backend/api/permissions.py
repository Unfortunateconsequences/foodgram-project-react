from rest_framework.permissions import BasePermission, SAFE_METHODS


class ReadOnly(BasePermission):
    def has_permission(self, request, view):
        return request.method in SAFE_METHODS


class IsOwnerOrReadOnly(BasePermission):

    def has_permission(self, request, view):
        return view.action == 'create' or request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        return (
            view.action in ('update', 'partial_update', 'destroy')
            and obj.author == request.user
        )
