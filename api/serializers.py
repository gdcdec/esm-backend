from rest_framework import serializers
from .models import Rubric

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