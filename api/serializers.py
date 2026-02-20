from rest_framework import serializers
from .models import Rubric
from .models import CustomUser

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

class CustomUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'patronymic', 'phone_number', 'city', 'street', 
            'house', 'apartment'
        ]
        extra_kwargs = {
            'password': {'write_only': True}
        }
    
    def create(self, validated_data):
        password = validated_data.pop('password', None)
        user = CustomUser.objects.create_user(**validated_data)
        if password:
            user.set_password(password)
        user.save()
        return user