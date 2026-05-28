from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed

from .models import BlacklistedToken, User, GuestUser
from .utils import decode_access_token


class CustomJWTAuthentication(BaseAuthentication):
    def authenticate(self, request):
        auth_header = request.headers.get ('Authorization')

        if not auth_header:
            return(GuestUser(), None)
        
        try:
            header, token = auth_header.split()
        except ValueError:
            return(GuestUser(), None)
        
        if header.lower() != 'bearer':
            return (GuestUser(), None)
        
        payload = decode_access_token(token)
        if not payload:
                    raise AuthenticationFailed('Невалидный или просроченный токен доступа.')
        
        jti = payload.get('jti')
        if jti:
            is_blacklisted = BlacklistedToken.objects.filter(token__jti=jti).exists()
            if is_blacklisted:
                raise AuthenticationFailed('Данный токен отозван (был произведен logout).')
        
        user_id = int(payload.get('sub'))
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