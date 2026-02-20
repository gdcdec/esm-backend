from django.db import models
from django.contrib.auth.models import AbstractUser
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
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    birth_date = models.DateField(blank=True, null=True)
    subscription_type = models.CharField(
        max_length=20,
        choices=[
            ('basic', 'Базовый'),
            ('premium', 'Премиум'),
            ('enterprise', 'Корпоративный'),
        ],
        default='basic'
    )
    
    def __str__(self):
        return self.username
    
    class Meta:
        db_table = 'custom_user'  # Явно указываем имя таблицы
        verbose_name = 'User'
        verbose_name_plural = 'Users'