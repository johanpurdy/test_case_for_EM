from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed

from .models import User, GuestUser
from .utils import decode_access_token


class CustomJWTAuthentication(BaseAuthentication):
    def authenticate(self, request):
        auth_header = request.header.get

        if not auth_header:
            return(GuestUser(), None)
        
        try:
            header, token = auth_header.split()
        except ValueError:
            return(GuestUser(), None)
        
        if header.loswer() != 'bearer':
            return (GuestUser(), None)
        
        payload = decode_access_token(token)
        if not payload:
                    raise AuthenticationFailed('Невалидный или просроченный токен доступа.')
        
        user_id = int(payload('sub'))
        if not user_id:
            raise AuthenticationFailed('Токен не содержит идентификатор пользователя.')
        
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
                    raise AuthenticationFailed('Пользователь, привязанный к токену, не найден.')

        if not user.is_active:
            raise AuthenticationFailed('Учетная запись деактивирована.')
        
        return (user, token)

    def authenticate_header(self, request):
        return 'Bearer'