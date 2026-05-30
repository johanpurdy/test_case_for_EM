from django.core.management.base import BaseCommand
from custom_auth.models import Role, Resource, CustomPermission, RolePermission, User
from custom_auth.utils import hash_password

class Command(BaseCommand):
    help = 'Наполнение базы данных стартовыми ролями, ресурсами и правами'

    def handle(self, *args, **options):
        self.stdout.write('Запуск наполнения БД тестовыми данными...')

        admin_role, _ = Role.objects.get_or_create(slug='admin', defaults={'name': 'Администратор'})
        user_role, _ = Role.objects.get_or_create(slug='user', defaults={'name': 'Пользователь'})
        manager_role, _ = Role.objects.get_or_create(slug='manager', defaults={'name': 'Менеджер'})

        doc_res, _ = Resource.objects.get_or_create(slug='documents', defaults={'name': 'Документы'})
        anal_res, _ = Resource.objects.get_or_create(slug='analytics', defaults={'name': 'Аналитика'})
        admin_res, _ = Resource.objects.get_or_create(slug='admin_panel', defaults={'name': 'Админ панель'})

        perms = {}
        for res in [doc_res, anal_res, admin_res]:
            perms[res.slug] = {}
            for action in ['read', 'create', 'update', 'delete']:
                perm, _ = CustomPermission.objects.get_or_create(
                    resource=res,
                    action=action
                )
                perms[res.slug][action] = perm


        RolePermission.objects.get_or_create(role=user_role, permission=perms['documents']['read'])

        RolePermission.objects.get_or_create(role=manager_role, permission=perms['documents']['read'])
        RolePermission.objects.get_or_create(role=manager_role, permission=perms['documents']['create'])
        RolePermission.objects.get_or_create(role=manager_role, permission=perms['documents']['update'])
        RolePermission.objects.get_or_create(role=manager_role, permission=perms['analytics']['read'])

        RolePermission.objects.get_or_create(role=admin_role, permission=perms['admin_panel']['read'])
        RolePermission.objects.get_or_create(role=admin_role, permission=perms['admin_panel']['create'])

        hashed_pwd = hash_password('password123')
        
        User.objects.get_or_create(
            email='admin@test.com',
            defaults={
                'first_name': 'Алексей', 'last_name': 'Админов', 
                'password_hash': hashed_pwd, 'role': admin_role, 'is_active': True
            }
        )
        User.objects.get_or_create(
            email='user@test.com',
            defaults={
                'first_name': 'Иван', 'last_name': 'Иванов', 
                'password_hash': hashed_pwd, 'role': user_role, 'is_active': True
            }
        )
        User.objects.get_or_create(
            email='manager@test.com',
            defaults={
                'first_name': 'Елена', 'last_name': 'Менеджерова', 
                'password_hash': hashed_pwd, 'role': manager_role, 'is_active': True
            }
        )

        self.stdout.write(self.style.SUCCESS('База данных успешно наполнена тестовыми данными!'))
