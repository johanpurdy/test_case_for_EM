import pytest
from django.urls import reverse
from rest_framework import status
from custom_auth.models import User, BlacklistedToken, RolePermission
from custom_auth.utils import generate_access_token
from django.test.client import Client
import time
from unittest.mock import patch


pytestmark = pytest.mark.django_db


def test_user_registration_success(api_client, db_setup):
    '''Успешная регистрация нового пользователя'''
    url = reverse('auth_register')
    data = {
        'first_name': 'Сергей',
        'last_name': 'Сергеев',
        'email': 'sergey@test.com',
        'password': 'secretpassword',
        'password_repeat': 'secretpassword'
    }
    response = api_client.post(url, data, format='json')
    assert response.status_code == status.HTTP_201_CREATED
    assert 'access_token' in response.data
    assert User.objects.filter(email='sergey@test.com').exists()

def test_user_registration_password_mismatch(api_client):
    '''Ошибка регистрации, если пароли не совпадают'''
    url = reverse('auth_register')
    data = {
        'first_name': 'Сергей',
        'last_name': 'Сергеев',
        'email': 'sergey@test.com',
        'password': 'password1',
        'password_repeat': 'password—другой'
    }
    response = api_client.post(url, data, format='json')
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert 'password_repeat' in response.data

def test_login_success(api_client, active_user):
    url = reverse('login')
    data = {'email': 'user@test.com', 'password': 'password123'}
    response = api_client.post(url, data, format='json')
    assert response.status_code == status.HTTP_200_OK
    assert 'access_token' in response.data

def test_login_inactive_user(api_client, active_user):
    active_user.is_active = False
    active_user.save()
    
    url = reverse('login')
    data = {'email': 'user@test.com', 'password': 'password123'}
    response = api_client.post(url, data, format='json')
    
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

def test_mock_resource_401_unauthorized(api_client):
    url = reverse('mock_documents')
    response = api_client.get(url)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

def test_mock_resource_200_success(api_client, active_user):
    token = generate_access_token(active_user.id)
    
    url = reverse('mock_documents')
    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
    
    response = api_client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert isinstance(response.data, list)

def test_mock_resource_403_forbidden(api_client, active_user):
    token = generate_access_token(active_user.id)
    
    url = reverse('mock_documents')
    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
    
    response = api_client.post(url, data={'title': 'New Doc'}, format='json')
    assert response.status_code == status.HTTP_403_FORBIDDEN

def test_admin_bypass_permissions(api_client, admin_user):
    token = generate_access_token(admin_user.id)
    
    url = reverse('mock_documents')
    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
    
    response = api_client.post(url, data={'title': 'Admin Doc'}, format='json')
    assert response.status_code == status.HTTP_201_CREATED

def test_logout_and_token_blacklisting(api_client, active_user):
    token = generate_access_token(active_user.id)
    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

    url_doc = reverse('mock_documents')
    assert api_client.get(url_doc).status_code == status.HTTP_200_OK

    url_logout = reverse('logout')
    logout_response = api_client.post(url_logout)
    assert logout_response.status_code == status.HTTP_200_OK

    assert BlacklistedToken.objects.count() == 1

    repeat_response = api_client.get(url_doc)
    assert repeat_response.status_code == status.HTTP_401_UNAUTHORIZED


def test_user_registration_email_exists(api_client, active_user):
    '''Ошибка регистрации, если email уже занят'''
    url = reverse('auth_register')
    data = {
        'first_name': 'Иван',
        'last_name': 'Иванов',
        'email': active_user.email,
        'password': 'secretpassword',
        'password_repeat': 'secretpassword'
    }
    response = api_client.post(url, data, format='json')
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert 'email' in response.data


def test_invalid_and_expired_token(api_client, active_user):
    '''Доступ запрещен с невалидным или просроченным токеном'''
    url = reverse('mock_documents')

    api_client.credentials(HTTP_AUTHORIZATION='Bearer invalid_token_string')
    response_invalid = api_client.get(url)
    assert response_invalid.status_code == status.HTTP_401_UNAUTHORIZED

    with patch('custom_auth.utils.time.time', return_value=time.time() - 86400):
        expired_token = generate_access_token(active_user.id)
        
    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {expired_token}')
    response_expired = api_client.get(url)
    assert response_expired.status_code == status.HTTP_401_UNAUTHORIZED


def test_update_profile_success(api_client, active_user):
    '''Успешное обновление своего профиля (PATCH /api/users/me/)'''
    token = generate_access_token(active_user.id)
    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
    
    url = reverse('user_me')
    data = {
        'first_name': 'Новое Имя',
        'last_name': 'Новая Фамилия'
    }
    response = api_client.patch(url, data, format='json')
    assert response.status_code == status.HTTP_200_OK
    
    active_user.refresh_from_db()
    assert active_user.first_name == 'Новое Имя'
    assert active_user.last_name == 'Новая Фамилия'


def test_delete_profile_success(api_client, active_user):
    '''Удаление или деактивация аккаунта (DELETE /api/users/me/)'''
    token = generate_access_token(active_user.id)
    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
    
    url = reverse('user_me')
    response = api_client.delete(url)

    assert response.status_code in [status.HTTP_200_OK, status.HTTP_204_NO_CONTENT]
    
    active_user.refresh_from_db()
    assert not active_user.is_active


def test_get_admin_rules_success(api_client, admin_user):
    '''Получение прав доступа администратором (GET /api/admin/rules/)'''
    token = generate_access_token(admin_user.id)
    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
    
    url = reverse('admin_rules')
    response = api_client.get(url)
    
    assert response.status_code == status.HTTP_200_OK
    assert 'access_matrix' in response.data
    assert isinstance(response.data['access_matrix'], dict)


def test_revoke_permissions_via_admin_rules(api_client, admin_user, active_user):
    """Отзыв прав у роли администратором (POST c allow=false)"""
    token = generate_access_token(admin_user.id)
    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
    
    url = reverse('admin_rules')
    grant_data = {
        "role_slug": active_user.role.slug,
        "resource_slug": "documents",
        "action": "create",
        "allow": True
    }
    api_client.post(url, grant_data, format='json')

    from custom_auth.models import CustomPermission, Resource
    resource = Resource.objects.get(slug="documents")
    permission = CustomPermission.objects.get(resource=resource, action="create")
    assert RolePermission.objects.filter(
        role=active_user.role,
        permission=permission
    ).exists()

    revoke_data = {
        "role_slug": active_user.role.slug,
        "resource_slug": "documents",
        "action": "create",
        "allow": False
    }
    response = api_client.post(url, revoke_data, format='json')
    assert response.status_code == status.HTTP_200_OK

    assert not RolePermission.objects.filter(
        role=active_user.role,
        permission=permission
    ).exists()
