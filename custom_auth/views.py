from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import AuthenticationFailed, NotAuthenticated

from custom_auth.permissions import CustomResourcePermission
from .serializers import ReadUserSerializer, UserLoginSerializer, UserRegisterSerializer, UserUpdateSerializer
from .utils import decode_access_token, generate_access_token, check_password
from rest_framework.permissions import (AllowAny)
from .models import BlacklistedToken, CustomPermission, OutstandingToken, Role, RolePermission, User


class RegisterUserView(APIView):

    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UserRegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            token = generate_access_token(user.id)
            return Response({
                'message': 'Пользователь успешно зарегистрирован.',
                'access_token': token,
                'user': ReadUserSerializer(user).data
            }, status=status.HTTP_201_CREATED)
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )
    

class LogoutUserView(APIView):
    def post(self, request):
        if not request.user or not request.user.is_authenticated:
            raise NotAuthenticated('Вы не вошли в систему.')
        
        raw_token = request.auth
        if not raw_token or not isinstance(raw_token, str):
            return Response({"detail": "Токен доступа не найден или неверного формата."}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        payload = decode_access_token(raw_token)
        if not payload:
            return Response({"detail": "Невалидный или просроченный токен."}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        jti = payload.get('jti')
        if not jti:
            return Response({"detail": "Идентификатор токена отсутствует."}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        try:
            outstanding_token = OutstandingToken.objects.get(jti=jti)
            BlacklistedToken.objects.get_or_create(token=outstanding_token)
            return Response({"detail": "Вы успешно вышли из системы."}, 
                          status=status.HTTP_200_OK)
        except OutstandingToken.DoesNotExist:
            return Response({"detail": "Токен не найден в реестре."}, 
                          status=status.HTTP_404_NOT_FOUND)
    
class LoginUserView(APIView):
     
    authentication_classes = []
    permission_classes = [AllowAny] 
     
    def post(self, request):
        serializer = UserLoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        email = serializer.validated_data['email']
        password = serializer.validated_data['password']

        user = User.objects.filter(email=email, is_active=True).first()

        if not user:
            return Response(
                {'detail': 'Неверный email или пароль.'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        right_password = check_password(password, user.password_hash)

        if not user or not right_password:
            return Response(
                {'detail': 'Неверный email или пароль.'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        token = generate_access_token(user.id)
        return Response({
            'access_token': token,
            'user': ReadUserSerializer(user).data
        }, status.HTTP_200_OK)
     
class UserProfileView(APIView):

    def _check_auth(self, request):
        if not request.user or not request.user.is_authenticated:
            raise NotAuthenticated('Вы не авторизованы.')

    def get(self, request):

        self._check_auth(request)
        serializer = ReadUserSerializer(request.user)
        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )

    def patch(self, request):
        self._check_auth(request)
        serializer = UserUpdateSerializer(
            request.user,
            data=request.data,
            partial=True
        )
        if serializer.is_valid():
            user = serializer.save()
            return Response(
                ReadUserSerializer(user).data,
                status=status.HTTP_200_OK
            )
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )

    def delete(self, request):
        self._check_auth(request)
        user = request.user
        user.is_active = False
        user.save()
        return Response(
            {'detail': 'Аккаунт деактивирован.'}, 
            status=status.HTTP_200_OK
        )
        

class AdminRulesView(APIView):
    permission_classes = [CustomResourcePermission]
    resource_slug = 'admin_panel'

    def get(self, request):
        '''Получение текущей карты доступов всех ролей'''
        roles = Role.objects.all()
        matrix = {}
        for role in roles:
            matrix[role.slug] = [
                {
                    'resource': rp.permission.resource.slug,
                    'action': rp.permission.action
                }
                for rp in RolePermission.objects.filter(role=role)
            ]
        return Response({'access_matrix': matrix}, status=status.HTTP_200_OK)

    def post(self, request):
        '''Добавление или отзыв прав у роли'''
        role_slug = request.data.get('role_slug')
        resource_slug = request.data.get('resource_slug')
        action = request.data.get('action')
        allow = request.data.get('allow', True)

        if not all([role_slug, resource_slug, action]):
            return Response(
                {'detail': 'Необходимы параметры: role_slug, resource_slug, action.'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            role = Role.objects.get(slug=role_slug)
            permission = CustomPermission.objects.get(resource__slug=resource_slug, action=action)
        except (Role.DoesNotExist, CustomPermission.DoesNotExist):
            return Response(
                {'detail': 'Роль или связка ресурс-действие не найдены.'}, 
                status=status.HTTP_404_NOT_FOUND
            )

        if allow:
            RolePermission.objects.get_or_create(role=role, permission=permission)
            msg = f'Роли "{role_slug}" выдано право "{action}" на ресурс "{resource_slug}".'
        else:
            RolePermission.objects.filter(role=role, permission=permission).delete()
            msg = f'У роли "{role_slug}" отозвано право "{action}" на ресурс "{resource_slug}".'

        return Response({'detail': msg}, status=status.HTTP_200_OK)


class MockDocumentView(APIView):
    permission_classes = [CustomResourcePermission]
    resource_slug = 'documents'

    MOCK_DATA = [
        {'id': 1, 'title': 'Отчет по продажам', 'confidential': True},
        {'id': 2, 'title': 'Инструкция для сотрудников', 'confidential': False}
    ]

    def get(self, request):
        return Response(self.MOCK_DATA, status=status.HTTP_200_OK)

    def post(self, request):
        return Response(
            {'detail': 'Документ сохранен (Mock).', 'data': request.data}, 
            status=status.HTTP_201_CREATED
        )


class MockAnalyticsView(APIView):
    permission_classes = [CustomResourcePermission]
    resource_slug = 'analytics'

    def get(self, request):
        return Response(
            {'metrics': {'users_count': 1250, 'active_sessions': 42}}, 
            status=status.HTTP_200_OK
        )