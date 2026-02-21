from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.auth import get_user_model
import random
from datetime import datetime, timedelta
# api/models.py
# Create your models here.


class Rubric(models.Model):
    """
    Модель для рубрик/категорий
    name является первичным ключом
    """
    name = models.CharField(
        max_length=100,
        primary_key=True,  # name становится первичным ключом
        verbose_name="Название рубрики",
        unique=True
    )
    counter = models.IntegerField(
        default=0,
        verbose_name="Счётчик",
        help_text="Количество элементов в рубрике"
    )
    
    class Meta:
        verbose_name = "Рубрика"
        verbose_name_plural = "Рубрики"
        ordering = ['name']  # сортировка по имени
    
    def __str__(self):
        return self.name
    
    def increment_counter(self):
        """Увеличить счётчик на 1"""
        self.counter += 1
        self.save()
    
    def decrement_counter(self):
        """Уменьшить счётчик на 1 (не ниже 0)"""
        if self.counter > 0:
            self.counter -= 1
            self.save()


class CustomUser(AbstractUser):
    """
    Поля что мы должны иметь по ТЗ
    Логин уже есть как гл ключ
    Пароль
    Почта
    Фамилия
    Имя
    Отчествво
    Номер телефона
    Город
    Улица
    Дом
    Квартира
    auth_token
    """
    
    birth_date = models.DateField(blank=True, null=True)
    # Добавляем недостающие поля
    patronymic = models.CharField(
        max_length=150, 
        blank=True, 
        null=True,
        verbose_name="Отчество"
    )
    
    phone_number = models.CharField(
        max_length=15, 
        blank=True, 
        null=True,
        verbose_name="Номер телефона"
    )
    
    city = models.CharField(
        max_length=100, 
        blank=True, 
        null=True,
        verbose_name="Город"
    )
    
    street = models.CharField(
        max_length=200, 
        blank=True, 
        null=True,
        verbose_name="Улица"
    )
    
    house = models.CharField(
        max_length=20, 
        blank=True, 
        null=True,
        verbose_name="Дом"
    )
    
    apartment = models.CharField(
        max_length=20, 
        blank=True, 
        null=True,
        verbose_name="Квартира"
    )
    """
    auth_token = models.CharField(
        max_length=255, 
        blank=True, 
        null=True,
        verbose_name="Токен авторизации"
    )
    """
    # Делаем email уникальным (ключевым полем)
    email = models.EmailField(
        unique=True,
        verbose_name="Почта"
    )
    
    def __str__(self):
        return self.username
    
    class Meta:
        db_table = 'custom_user'  # Явно указываем имя таблицы
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        
User = get_user_model()

class PasswordReset(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    
    @classmethod
    def generate_code(cls):
        """Генерирует 6-значный код"""
        return ''.join([str(random.randint(0, 9)) for _ in range(6)])
    
    @classmethod
    def create_for_user(cls, user):
        """Создает код для пользователя"""
        # Удаляем старые коды пользователя
        cls.objects.filter(user=user).delete()
        
        # Создаем новый код
        code = cls.generate_code()
        expires_at = datetime.now() + timedelta(minutes=15)  # Код действителен 15 минут
        
        return cls.objects.create(
            user=user,
            code=code,
            expires_at=expires_at
        )
    
    def is_valid(self):
        """Проверяет, действителен ли код"""
        return (not self.is_used and 
                self.expires_at > datetime.now())
    
    def __str__(self):
        return f"{self.user.username} - {self.code}"

