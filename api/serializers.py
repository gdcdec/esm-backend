from rest_framework import serializers
from .models import Rubric
from .models import CustomUser
from .models import PasswordReset
from django.contrib.auth import get_user_model

User = get_user_model()


class RubricSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rubric
        fields = ['name', 'counter']  # id не нужен, так как name - это и есть первичный ключ
        read_only_fields = ['counter']  # счётчик только для чтения через API
    
    def validate_name(self, value):
        """Валидация имени рубрики"""
        if len(value) < 2:
            raise serializers.ValidationError("Название рубрики должно быть не короче 2 символов")
        if len(value) > 100:
            raise serializers.ValidationError("Название рубрики должно быть не длиннее 100 символов")
        return value

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, style={'input_type': 'password'})
    password2 = serializers.CharField(write_only=True, style={'input_type': 'password'}, label="Подтверждение пароля")
    
    class Meta:
        model = CustomUser
        fields = [
            'username', 'email', 'password', 'password2',
            'first_name', 'last_name', 'patronymic',
            'phone_number', 'city', 'street', 'house', 'apartment'
        ]
        extra_kwargs = {
            'email': {'required': True},
        }
    
    def validate(self, data):
        if data['password'] != data['password2']:
            raise serializers.ValidationError("Пароли не совпадают")
        return data
    
    def validate_email(self, value):
        if CustomUser.objects.filter(email=value).exists():
            raise serializers.ValidationError("Пользователь с таким email уже существует")
        return value
    
    def create(self, validated_data):
        # Удаляем password2
        validated_data.pop('password2')
        
        # ВАЖНО: Используем create_user, а не create!
        # create_user хеширует пароль, create - сохраняет как есть
        user = CustomUser.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],  # Пароль будет захэширован
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            patronymic=validated_data.get('patronymic', ''),
            phone_number=validated_data.get('phone_number', ''),
            city=validated_data.get('city', ''),
            street=validated_data.get('street', ''),
            house=validated_data.get('house', ''),
            apartment=validated_data.get('apartment', '')
        )
        
        return user
    


class PasswordResetRequestSerializer(serializers.Serializer):
    """Сериализатор для запроса сброса пароля"""
    email = serializers.EmailField()
    
    def validate_email(self, value):
        try:
            user = User.objects.get(email=value)
            # Сохраняем пользователя в контексте для использования в view
            self.context['user'] = user
        except User.DoesNotExist:
            raise serializers.ValidationError("Пользователь с таким email не найден")
        return value

class PasswordResetVerifySerializer(serializers.Serializer):
    """Сериализатор для проверки кода"""
    email = serializers.EmailField()
    code = serializers.CharField(max_length=6)
    
    def validate(self, data):
        try:
            user = User.objects.get(email=data['email'])
            reset = PasswordReset.objects.get(
                user=user,
                code=data['code'],
                is_used=False
            )
            
            if not reset.is_valid():
                raise serializers.ValidationError("Код истек. Запросите новый код.")
            
            # Сохраняем в контексте
            self.context['reset'] = reset
            
        except User.DoesNotExist:
            raise serializers.ValidationError("Пользователь не найден")
        except PasswordReset.DoesNotExist:
            raise serializers.ValidationError("Неверный код")
        
        return data

class PasswordResetConfirmSerializer(serializers.Serializer):
    """Сериализатор для установки нового пароля"""
    email = serializers.EmailField()
    code = serializers.CharField(max_length=6)
    new_password = serializers.CharField(min_length=6, write_only=True)
    confirm_password = serializers.CharField(min_length=6, write_only=True)
    
    def validate(self, data):
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError("Пароли не совпадают")
        
        try:
            user = User.objects.get(email=data['email'])
            reset = PasswordReset.objects.get(
                user=user,
                code=data['code'],
                is_used=False
            )
            
            if not reset.is_valid():
                raise serializers.ValidationError("Код истек. Запросите новый код.")
            
            # Сохраняем в контексте
            self.context['user'] = user
            self.context['reset'] = reset
            
        except User.DoesNotExist:
            raise serializers.ValidationError("Пользователь не найден")
        except PasswordReset.DoesNotExist:
            raise serializers.ValidationError("Неверный код")
        
        return data