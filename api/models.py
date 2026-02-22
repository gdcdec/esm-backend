from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.auth import get_user_model
import random
from datetime import datetime, timedelta
from .validators import validate_image_size, validate_image_extension
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
User = get_user_model()# По сути экспорт как модель


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


# Контент
class Post(models.Model):
    """
    Модель поста с заголовком, описанием, фотографиями и датами
    """
    # Основные поля
    title = models.CharField(
        max_length=200,
        verbose_name="Заголовок",
        help_text="Краткий заголовок поста (макс. 200 символов)",
        null=True,  # Временно разрешаем NULL
        blank=True  # Временно разрешаем пустое значение
    )
    
    description = models.TextField(
        verbose_name="Описание",
        help_text="Полное описание или содержание поста",
        blank=True  # Можно оставить пустым
    )
    
    # СВЯЗЬ С РУБРИКОЙ
    rubric = models.ForeignKey(
        Rubric,
        on_delete=models.SET_NULL,  # При удалении рубрики, поле станет NULL
        null=True,                  # Разрешаем NULL 
        blank=True,
        related_name='posts',        # Обратная связь: rubric.posts.all()
        verbose_name="Рубрика",
        help_text="Рубрика/категория поста"
    )
    
    # Адрес события
    address = models.CharField(
        max_length=500,
        verbose_name="Адрес события",
        help_text="Адрес инцидента/события",
        blank=True
    )
    
    # Координаты (точка на карте). Временно null/blank
    latitude = models.FloatField(
        null=True,
        blank=True,
        verbose_name="Широта",
        help_text="Latitude: -90 до 90"
    )
    longitude = models.FloatField(
        null=True,
        blank=True,
        verbose_name="Долгота",
        help_text="Longitude: -180 до 180"
    )
    
    # СВЯЗЬ С АВТОРОМ # После продак убрать нулы
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='posts',
        verbose_name="Автор",
        null=True,  # Временно разрешаем NULL
        blank=True  # Временно разрешаем пустое значение
    )
    
    # Статус поста (опционально, для публикации/черновика)
    STATUS_CHOICES = [
        ('draft', 'Черновик'),
        ('published', 'Опубликован'),
        ('archived', 'В архиве'),
    ]
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='published',
        verbose_name="Статус"
    )
    
    # Дата создания - автоматически при создании
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата создания",
        null=True,  # Временно разрешаем NULL
        blank=True  # Временно разрешаем пустое значение
    )
    
    # Дата обновления - автоматически при каждом сохранении
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Дата обновления"
    )
    
    # Дата публикации
    published_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Дата публикации"
    )
    
    # Поле для мягкого удаления
    is_deleted = models.BooleanField(
        default=False,
        verbose_name="Удален"
    )
    
    class Meta:
        ordering = ['-created_at', '-published_at']  # Сортировка по умолчанию
        verbose_name = "Пост"
        verbose_name_plural = "Посты"
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['author', '-created_at']),
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['rubric']),
        ]
    
    def __str__(self):
        return f"Пост #{self.id}: {self.title[:50]}"
    
    def save(self, *args, **kwargs):
            # Если статус меняется на 'published' и не установлена дата публикации
            if self.status == 'published' and not self.published_at:
                from django.utils import timezone
                self.published_at = timezone.now()
            super().save(*args, **kwargs)
            # Обновляем счетчик рубрики при изменении
            old = None
            if self.pk:
                old = Post.objects.get(pk=self.pk)
            
            super().save(*args, **kwargs)
            
            # Обновляем счетчики рубрик
            if old and old.rubric != self.rubric:
                if old.rubric:
                    old.rubric.decrement_counter()
                if self.rubric:
                    self.rubric.increment_counter()
            elif not old and self.rubric:
                self.rubric.increment_counter()
    
    def delete(self, *args, **kwargs):
        # Уменьшаем счетчик при удалении
        if self.rubric:
            self.rubric.decrement_counter()
        super().delete(*args, **kwargs)
    
    @property
    def photo_count(self):
        """Количество фотографий в посте"""
        return self.photos.count()
    
    @property
    def first_photo(self):
        """Первая фотография поста (для превью)"""
        return self.photos.first()


class PostPhoto(models.Model):
    """
    Модель фотографии поста
    """
    # СВЯЗЬ С ПОСТАМИ
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='photos',
        verbose_name="Пост"
    )
    
    photo = models.ImageField(
        upload_to='posts/%Y/%m/%d/',
        validators=[validate_image_size, validate_image_extension],
        verbose_name="Фотография"
    )
    
    # Порядковый номер для сортировки
    order = models.PositiveIntegerField(
        default=0,
        verbose_name="Порядок"
    )
    
    # Подпись к фото
    caption = models.CharField(
        max_length=200,
        blank=True,# Я не думаю, что при загрузке они будут каждое фото описывать, в serializer тоже обусловится
        verbose_name="Подпись"
    )
    
    uploaded_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата загрузки"
    )
    
    class Meta:
        ordering = ['order', 'id']
        verbose_name = "Фотография поста"
        verbose_name_plural = "Фотографии поста"
    
    def __str__(self):
        return f"Фото {self.order} для поста #{self.post_id}"
    
    def delete(self, *args, **kwargs):
        # При удалении записи удаляем и файл
        if self.photo:
            storage = self.photo.storage
            if storage.exists(self.photo.name):
                storage.delete(self.photo.name)
        super().delete(*args, **kwargs)
