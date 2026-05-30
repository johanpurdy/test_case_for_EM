# Custom Auth System

Собственная система аутентификации и авторизации на Django REST Framework.

## Технологии

- Python 3.12
- Django 5.x
- Django REST Framework
- PostgreSQL 14
- Docker / Docker Compose
- JWT (JSON Web Tokens)

## Функциональность

### 2. Система разграничения прав доступа
- Собственная модель прав доступа
- Роли: `admin`, `manager`, `user`
- API для управления правами (только для администратора)
- Проверка доступа к ресурсам (401/403 ошибки)

## Схема базы данных

### Таблица `custom_auth_user`
| Поле | Тип | Описание |
|------|-----|----------|
| id | Integer | Первичный ключ |
| email | EmailField | Уникальный email пользователя |
| first_name | CharField | Имя |
| last_name | CharField | Фамилия |
| patronymic | CharField | Отчество (опционально) |
| password_hash | CharField | Хэш пароля |
| is_active | BooleanField | Активен/удален (мягкое удаление) |
| created_at | DateTimeField | Дата регистрации |
| role | FK(Role) | Ссылка на роль |

### Таблица `custom_auth_role`
| Поле | Тип | Описание |
|------|-----|----------|
| id | Integer | Первичный ключ |
| name | CharField | Название роли (Администратор, Менеджер, Пользователь) |
| slug | SlugField | Идентификатор (admin, manager, user) |

### Таблица `custom_auth_resource`
| Поле | Тип | Описание |
|------|-----|----------|
| id | Integer | Первичный ключ |
| name | CharField | Название ресурса |
| slug | SlugField | Идентификатор (documents, analytics, admin_panel) |

### Таблица `custom_auth_custompermission`
| Поле | Тип | Описание |
|------|-----|----------|
| id | Integer | Первичный ключ |
| resource | FK(Resource) | Ссылка на ресурс |
| action | CharField | Действие (create, read, update, delete) |

### Таблица `custom_auth_rolepermission`
| Поле | Тип | Описание |
|------|-----|----------|
| id | Integer | Первичный ключ |
| role | FK(Role) | Ссылка на роль |
| permission | FK(CustomPermission) | Ссылка на право доступа |

### Связи
- User → Role (прямая связь через поле role)
- Role → RolePermission → CustomPermission → Resource

## Запуск проекта

В преокте реализован запуск локально(через терминал и manage.py) и через Docker

### Запуск через Docker
1. Настройте переменные окружения: Создайте файл .env в корне проекта и наполните данными
Пример: 
```
SECRET_KEY = 'example'
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

POSTGRES_DB=auth_project_db
POSTGRES_USER=auth_project_user
POSTGRES_PASSWORD=auth_project_password
DB_HOST=db
DB_PORT=5432
```
Если нет ключа SECRET_KEY, оставьте поле пустым метод ```get_random_secret_key()``` сгененрирует его за вас.

2. Запустите контейнеры: 
```
docker-compose up --build
```

### Запуск локально
1. Создайте и активируйте виртуальное окружение: python -m venv venv
```
Windows:
venv\Scripts\activate

Linux/Mac:
source venv/bin/activate
```
2. Установите зависимости: pip install -r requirements.txt
3. Настройте переменные окружения: Создайте файл .env в корне проекта и наполните данными
Пример: 
```
SECRET_KEY = 'example'
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
```
Если нет ключа SECRET_KEY, оставьте поле пустым метод ```get_random_secret_key()``` сгененрирует его за вас.
4. В файле settings.py закомментируте блок:
```
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('POSTGRES_DB', 'django'),
        'USER': os.getenv('POSTGRES_USER', 'django'),
        'PASSWORD': os.getenv('POSTGRES_PASSWORD', ''),
        'HOST': os.getenv('DB_HOST', ''),
        'PORT': os.getenv('DB_PORT', 5432)
    }
}
```
5. Расскоментируйте блок:
```
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}
```
6. Создайте миграции:
```
python manage.py makemigrations
```
7. Выполните миграции:
```
python manage.py migrate
```
8. Добавьте тестовые данные
```
python manage.py seed_data
```
