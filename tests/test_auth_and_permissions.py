import pytest
from django.urls import reverse
from rest_framework import status
from custom_auth.models import User, BlacklistedToken, RolePermission
from .utils import generate_access_token

pytestmark = pytest.mark.django_db


def test_user_registration_success(api_client, db_setup):
    """Успешная регистрация нового пользователя"""
    url = reverse('auth_register')
    data = {
        "first_name": "Сергей",
        "last_name": "Сергеев",
        "email": "sergey@test.com",
        "password": "secretpassword",
        "password_repeat": "secretpassword"
    }
    response = api_client.post(url, data, format='json')
    assert response.status_code == status.HTTP_201_CREATED
    assert "access_token" in response.data
    assert User.objects.filter(email="sergey@test.com").exists()

def test_user_registration_password_mismatch(api_client):
    """Ошибка регистрации, если пароли не совпадают"""
    url = reverse('auth_register')
    data = {
        "first_name": "Сергей",
        "last_name": "Сергеев",
        "email": "sergey@test.com",
        "password": "password1",
        "password_repeat": "password—другой"
    }
    response = api_client.post(url, data, format='json')
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "password_repeat" in response.data

def test_login_success(api_client, active_user):
    url = reverse('login')
    data = {"email": "user@test.com", "password": "password123"}
    response = api_client.post(url, data, format='json')
    assert response.status_code == status.HTTP_200_OK
    assert "access_token" in response.data

def test_login_inactive_user(api_client, active_user):
    active_user.is_active = False
    active_user.save()
    
    url = reverse('login')
    data = {"email": "user@test.com", "password": "password123"}
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
    
    response = api_client.post(url, data={"title": "New Doc"}, format='json')
    assert response.status_code == status.HTTP_403_FORBIDDEN

def test_admin_bypass_permissions(api_client, admin_user):
    token = generate_access_token(admin_user.id)
    
    url = reverse('mock_documents')
    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
    
    response = api_client.post(url, data={"title": "Admin Doc"}, format='json')
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
