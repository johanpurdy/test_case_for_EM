from django.db import models

class User(models.Model):
    first_name = models.CharField(
        'Имя',
        max_length=150,
    )
    last_name = models.CharField(
        'Фамилия',
        max_length=150,
    )
    email = models.EmailField(
        'email address',
        max_length=254,
        unique=True,
    )
    password_hash = models.CharField(
        'Пароль',
        max_length=255
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def is_authenticated(self):
        return True

    class Meta:
        ordering = ('created_at',)
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return f'{self.first_name} {self.last_name}'


class Roles(models.Model):
    name = models.CharField(
        'Название',
        max_length=32,
        unique=True,
    )
    slug = models.SlugField(
        'Идентификатор для URL',
        max_length=32,
        unique=True,
    )
    users = models.ManyToManyField(
        User,
        through='UserRoles',
        related_name='roles'
    )

    class Meta:
        verbose_name = 'Роль'
        verbose_name_plural = 'Роли'
        ordering = ('name',)

    def __str__(self):
        return self.name


class UserRoles(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )
    role = models.ForeignKey(
        Roles,
        on_delete=models.CASCADE
    )

    class Meta:
        verbose_name = 'Роль Пользователя'
        verbose_name_plural = 'Роли Пользователей'
        unique_together = ('user', 'role')


class Resource(models.Model):
    slug = models.SlugField(
        'Идентификатор для URL',
        max_length=32,
        unique=True,
    )
    name = models.CharField(
        'Название бизнес - ресурса',
        max_length=100
    )

    class Meta:
        verbose_name = 'Бизнес - Ресурс'
        verbose_name_plural = 'Бизнес - Ресурсы'


class Permission(models.Model):
    ACTION_CHOICES = [
        ('create', 'Create'),
        ('read', 'Read'),
        ('update', 'Update'),
        ('delete', 'Delete'),
    ]
    resource = models.ForeignKey(
        Resource,
        on_delete=models.CASCADE,
        related_name='permissions'
    )
    action = models.CharField(
        'Действия',
        max_length=20,
        choices=ACTION_CHOICES
    )
    roles = models.ManyToManyField(
        Roles,
        through='RolePermission',
        related_name='permissions'
    )

    class Meta:
        verbose_name = 'Разрешение'
        verbose_name_plural = 'Разрешения'
        unique_together = ('resource', 'action')


class RolePermission(models.Model):
    role = models.ForeignKey(
        Roles,
        on_delete=models.CASCADE
    )
    permission = models.ForeignKey(
        Permission,
        on_delete=models.CASCADE
    )

    class Meta:
        verbose_name = 'Разрешение для Роли'
        verbose_name_plural = 'Разрешения для Ролей'
        unique_together = ('role', 'permission')


class GuestUser:
    id = None
    email = None
    first_name = ''
    last_name = ''

    @property
    def is_authenticated(self):
        return False

    def __str__(self):
        return "Анонимный пользователь (Гость)"