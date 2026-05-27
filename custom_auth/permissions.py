from rest_framework.permissions import BasePermission
from rest_framework.exceptions import PermissionDenied, NotAuthenticated
from .models import CustomPermission, RolePermission

class CustomResourcePermission(BasePermission):
    def has_permission(self, request, view):

        user = request.user

        if not user or not user.is_authenticated:
            raise NotAuthenticated('Вы не авторизованы.')

        if user.role and user.role.slug == 'admin':
            return True

        actions = {choice[0]: choice[0] for choice in CustomPermission.ACTION_CHOICES}
        
        method_map = {
            'GET': actions.get('read'),
            'POST': actions.get('create'),
            'PUT': actions.get('update'),
            'PATCH': actions.get('update'),
            'DELETE': actions.get('delete')
        }
        
        required_action = method_map.get(request.method)
        target_resource_slug = getattr(view, 'resource_slug', None)
        
        if not target_resource_slug or not required_action:
            raise PermissionDenied('Доступ запрещен')
        
        user_has_access = RolePermission.objects.filter(
            role=user.role,
            permission__resource__slug=target_resource_slug,
            permission__action=required_action
        ).exists()

        if not user_has_access:
            raise PermissionDenied('Доступ запрещен')
        
        return True 
