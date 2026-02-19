from django.db import models
from django.contrib.auth.models import User
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