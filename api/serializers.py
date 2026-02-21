from rest_framework import serializers
from .models import Rubric
from .models import CustomUser
from .models import PasswordReset
from .models import Post, PostPhoto
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
        # Удаляем password2 и теперь с проверкой, если фронты не отправят
        if validated_data['password2']:
            validated_data.pop('password2')
        
        
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
    
    
# Posts
class PostPhotoSerializer(serializers.ModelSerializer):
    """Сериализатор для фотографий поста"""
    photo_url = serializers.SerializerMethodField()
    
    class Meta:
        model = PostPhoto
        fields = ['id', 'photo', 'photo_url', 'order', 'caption', 'uploaded_at']
        extra_kwargs = {
            'photo': {'write_only': True},
        }
    
    def get_photo_url(self, obj):
        request = self.context.get('request')
        if obj.photo and request:
            return request.build_absolute_uri(obj.photo.url)
        return None


class PostSerializer(serializers.ModelSerializer):
    """
    Полный сериализатор для поста
    """
    author_username = serializers.CharField(source='author.username', read_only=True)
    author_email = serializers.EmailField(source='author.email', read_only=True)
    photos = PostPhotoSerializer(many=True, read_only=True)
    photo_count = serializers.IntegerField(read_only=True)
    first_photo = serializers.SerializerMethodField()
    
    class Meta:
        model = Post
        fields = [
            'id',                # Номер поста/сообщения
            'title',              # Тема сообщения (заголовок)
            'description',        # Текст сообщения
            'address',            # Адрес события (по ТЗ)
            'latitude',           # Широта (координаты)
            'longitude',          # Долгота (координаты)
            'author',             # ID автора
            'author_username',    # Имя автора
            'author_email',       # Email автора
            'status',             # Статус
            'created_at',         # Дата создания
            'updated_at',         # Дата обновления
            'published_at',       # Дата публикации
            'photos',             # Список фото
            'photo_count',        # Количество фото (подпись по ТЗ)
            'first_photo',        # Первое фото — главное (по ТЗ)
        ]
        read_only_fields = ['author', 'created_at', 'updated_at', 'published_at']
    
    def get_first_photo(self, obj):
        """Возвращает первую фотографию для превью"""
        first = obj.photos.first()
        if first:
            return PostPhotoSerializer(first, context=self.context).data
        return None


class PostCreateSerializer(serializers.ModelSerializer):
    """
    Сериализатор для создания поста/сообщения (по ТЗ)
    """
    class Meta:
        model = Post
        fields = ['title', 'description', 'address', 'latitude', 'longitude', 'status']
    
    def create(self, validated_data):
        validated_data['author'] = self.context['request'].user
        return super().create(validated_data)


class PostUpdateSerializer(serializers.ModelSerializer):
    """
    Сериализатор для обновления поста/сообщения
    """
    class Meta:
        model = Post
        fields = ['title', 'description', 'address', 'latitude', 'longitude', 'status']


class PostPhotoUploadSerializer(serializers.Serializer):
    """
    Сериализатор для загрузки фотографий к посту
    """
    post_id = serializers.IntegerField()
    photos = serializers.ListField(
        child=serializers.ImageField(),
        write_only=True
    )
    captions = serializers.ListField(
        child=serializers.CharField(required=False, allow_blank=True),
        required=False
    )
    
    def validate_post_id(self, value):
        try:
            post = Post.objects.get(id=value)
            if post.author != self.context['request'].user:
                raise serializers.ValidationError("Вы не автор этого поста")
        except Post.DoesNotExist:
            raise serializers.ValidationError("Пост не найден")
        return value
    
    def validate(self, data):
        
        # Фото без подписей
        if 'captions' in data and data['captions']:
            # Если подписи есть, проверяем их количество только если они не пустые
            if len(data['captions']) != len(data['photos']):
                raise serializers.ValidationError(
                    "Количество подписей должно соответствовать количеству фотографий"
                )
        return data
    
    def create(self, validated_data):
        post = Post.objects.get(id=validated_data['post_id'])
        photos = validated_data['photos']
        
        # Если подписей нет, создаем пустой список
        captions = validated_data.get('captions', [])
        
        # Если подписей меньше чем фото, дополняем пустыми строками
        if len(captions) < len(photos):
            captions.extend([''] * (len(photos) - len(captions)))
        
        created_photos = []
        for index, (photo, caption) in enumerate(zip(photos, captions)):
            post_photo = PostPhoto.objects.create(
                post=post,
                photo=photo,
                order=index,
                caption=caption or ''  # Если caption None, используем пустую строку
            )
            created_photos.append(post_photo)
        
        return created_photos


class PostListSerializer(serializers.ModelSerializer):
    """
    Упрощённый сериализатор для списка сообщений
    тема сообщения, адрес, главная фотография
    """
    author_username = serializers.CharField(source='author.username')
    photo_count = serializers.IntegerField(read_only=True)
    preview_photo = serializers.SerializerMethodField()
    
    class Meta:
        model = Post
        fields = [
            'id', 'title', 'address', 'latitude', 'longitude',
            'author_username', 'created_at', 'photo_count', 'preview_photo'
        ]
    
    def get_preview_photo(self, obj):
        """Возвращает полный URL первого (главного) фото для превью"""
        first = obj.photos.first()
        if first and first.photo:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(first.photo.url)
            return first.photo.url
        return None


# === Nominatim / адреса ===
class AddressReverseSerializer(serializers.Serializer):
    """Запрос обратного геокодирования: координаты → адрес"""
    lat = serializers.FloatField(min_value=-90, max_value=90)
    lon = serializers.FloatField(min_value=-180, max_value=180)


class AddressSearchSerializer(serializers.Serializer):
    """Поиск по имени/адресу"""
    q = serializers.CharField(min_length=2, max_length=200)
    limit = serializers.IntegerField(default=5, min_value=1, max_value=10)