from rest_framework import serializers
from .models import User, Role, Resource, CustomPermission
from .utils import hash_password


class UserRegisterSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(label='Email адрес')

    password = serializers.CharField(
        write_only=True, 
        min_length=6, 
        style={'input_type': 'password'},
        label='Пароль'
    )
    password_repeat = serializers.CharField(
        write_only=True, 
        min_length=6, 
        style={'input_type': 'password'},
        label='Повторите пароль'
    )

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'patronymic', 'email', 'password', 'password_repeat']

    def validate(self, data):
        if data['password'] != data['password_repeat']:
            raise serializers.ValidationError({'password_repeat': 'Введенные пароли не совпадают.'})

        if User.objects.filter(email=data['email'], is_active=True).exists():
            raise serializers.ValidationError({'email': 'Пользователь с таким email уже существует.'})
            
        return data
    
    def create(self, validated_data):
        validated_data.pop('password_repeat')
        raw_password = validated_data.pop('password')
        validated_data['password_hash'] = hash_password(raw_password)
        
        inactive_user = User.objects.filter(email=validated_data['email'], is_active=False).first()

        default_role, _ = Role.objects.get_or_create(
            slug='user', 
            defaults={'name': 'Пользователь'}
        )
        validated_data['role'] = default_role

        if inactive_user:
            validated_data.pop('email', None)
            for attr, value in validated_data.items():
                setattr(inactive_user, attr, value)

            inactive_user.is_active = True
            inactive_user.save()
            return inactive_user

        return super().create(validated_data)

class UserLoginSerializer(serializers.Serializer):
    email = serializers.EmailField(label='Email адрес')
    password = serializers.CharField(
        write_only=True, 
        style={'input_type': 'password'},
        label='Пароль'
    )


class UserUpdateSerializer(serializers.ModelSerializer):

    email = serializers.EmailField(required=False)

    password = serializers.CharField(
        write_only=True, 
        required=False,
        min_length=6, 
        style={'input_type': 'password'},
        label='Новый пароль'
    )

    class Meta:
        model = User
        fields = ['first_name', 'patronymic', 'last_name', 'email', 'password']
        extra_kwargs = {
            'first_name': {'required': False},
            'last_name': {'required': False},
            'email': {'required': False},
        }

    def validate_email(self, value):
        if not self.instance:
            return value

        current_user = self.instance.id
        if User.objects.filter(email=value, is_active=True).exclude(id=current_user).exists():
            raise serializers.ValidationError('Пользователь с таким email уже существует.')
        return value

    def update(self, instance, validated_data):
        if 'password' in validated_data:
            raw_password = validated_data.pop('password')
            validated_data['password_hash'] = hash_password(raw_password)
        return super().update(instance, validated_data)
    

class ResourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Resource
        fields = ['id', 'slug', 'name']


class CustomPermissionSerializer(serializers.ModelSerializer):
    resource = ResourceSerializer(read_only = True)
    
    class Meta:
        model = CustomPermission
        fields = ['id', 'action', 'resource']


class RoleSerializer(serializers.ModelSerializer):
    permissions = CustomPermissionSerializer(many = True, read_only = True)

    class Meta:
        model = Role
        fields = ['id', 'name', 'slug', 'permissions']


class ReadUserSerializer(serializers.ModelSerializer):
    role = RoleSerializer(read_only = True)

    class Meta:
        model = User
        fields = ['id', 'first_name', 'patronymic', 'last_name', 'email', 'role', 'created_at']
        read_only_fields = fields



