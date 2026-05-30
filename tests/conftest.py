import pytest
from datetime import datetime, timedelta, timezone
from django.utils import timezone as django_timezone
from custom_auth.models import User, Role, Resource, CustomPermission, RolePermission, OutstandingToken
from custom_auth.utils import hash_password, generate_access_token
from rest_framework.test import APIClient

@pytest.fixture
def db_setup(db):

    admin_role = Role.objects.create(name='Администратор', slug='admin')
    user_role = Role.objects.create(name='Пользователь', slug='user')

    doc_resource = Resource.objects.create(name='Документы', slug='documents')
    admin_resource = Resource.objects.create(name='Админ панель', slug='admin_panel')

    read_doc_perm = CustomPermission.objects.create(resource=doc_resource, action='read')
    create_doc_perm = CustomPermission.objects.create(resource=doc_resource, action='create')
    admin_perm = CustomPermission.objects.create(resource=admin_resource, action='read')

    RolePermission.objects.create(role=user_role, permission=read_doc_perm)
    
    return {
        'roles': {'admin': admin_role, 'user': user_role},
        'resources': {'documents': doc_resource, 'admin_panel': admin_resource},
        'permissions': {'read_doc': read_doc_perm, 'create_doc': create_doc_perm}
    }

@pytest.fixture
def active_user(db_setup):
    return User.objects.create(
        first_name='Иван',
        last_name='Иванов',
        email='user@test.com',
        password_hash=hash_password('password123'),
        role=db_setup['roles']['user'],
        is_active=True
    )

@pytest.fixture
def admin_user(db_setup):
    """Фикстура администратора"""
    return User.objects.create(
        first_name='Петр',
        last_name='Петров',
        email='admin@test.com',
        password_hash=hash_password('admin123'),
        role=db_setup['roles']['admin'],
        is_active=True
    )

@pytest.fixture
def api_client():
    return APIClient()
