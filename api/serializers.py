from rest_framework import serializers
from .models import Rubric
from .models import CustomUser
from .models import PasswordReset
from .models import Post, PostPhoto
from django.contrib.auth import get_user_model
from .validators import (
    validate_username, validate_password_strength, validate_email_strict,
    validate_phone_number, validate_first_name, validate_last_name,
    validate_patronymic, validate_street, validate_house, validate_apartment,
    validate_city, validate_title_length, validate_description_length
)

User = get_user_model()


class RubricSerializer(serializers.ModelSerializer):
    # Добавляем поле для отображения URL фото
    photo_url = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = Rubric
        fields = [
            'name',           # первичный ключ
            'counter',        # счётчик
            'photo',          # поле для загрузки фото
            'photo_url',      # URL для отображения фото (только для чтения)
        ]
        read_only_fields = ['counter']  # counter обновляется только через методы
    
    def get_photo_url(self, obj):
        """Возвращает URL фото или None"""
        return obj.get_photo_url()
    
    def validate_photo(self, value):
        """Валидация фото"""
        if value:
            # Проверка размера (макс 5MB)
            if value.size > 5 * 1024 * 1024:
                raise serializers.ValidationError("Размер фото не должен превышать 5MB")
            
            # Проверка типа файла
            allowed_types = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
            if value.content_type not in allowed_types:
                raise serializers.ValidationError(
                    f"Поддерживаются только: {', '.join(allowed_types)}"
                )
        return value

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True, 
        style={'input_type': 'password'},
        validators=[validate_password_strength] 
    )
    password2 = serializers.CharField(
        write_only=True, 
        style={'input_type': 'password'}, 
        label="Подтверждение пароля"
    )
    username = serializers.CharField(
        validators=[validate_username]
    )
    email = serializers.EmailField(
        validators=[validate_email_strict]
    )
    first_name = serializers.CharField(
        validators=[validate_first_name]
    )
    last_name = serializers.CharField(
        validators=[validate_last_name]
    )
    patronymic = serializers.CharField(
        required=False,
        allow_blank=True,
        validators=[validate_patronymic]
    )
    phone_number = serializers.CharField(
        validators=[validate_phone_number]
    )
    city = serializers.CharField(
        required=False,
        allow_blank=True,
        validators=[validate_city]
    )
    street = serializers.CharField(
        required=False,
        allow_blank=True,
        validators=[validate_street]
    )
    house = serializers.CharField(
        required=False,
        allow_blank=True,
        validators=[validate_house]
    )
    apartment = serializers.CharField(
        required=False,
        allow_blank=True,
        validators=[validate_apartment]
    )
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
        # Проверка совпадения паролей можно снять, если в фронте проверяют
        if data['password'] and data['password2']:
            if data['password'] != data['password2']:
                raise serializers.ValidationError({"password2": "Пароли не совпадают"})
        
        # Проверка уникальности username
        if CustomUser.objects.filter(username=data['username']).exists():
            raise serializers.ValidationError({"username": "Пользователь с таким логином уже существует"})
        
        return data
    
    def validate_email(self, value):
        if CustomUser.objects.filter(email=value).exists():
            raise serializers.ValidationError("Пользователь с таким email уже существует")
        return value
    
    def validate_city(self, value):
        # Автоматически устанавливаем Самару для MVP если друг пусто, хотя малоли что это сломает)
        if value:
            return value
        else:
            return "Самара"
    
    def create(self, validated_data):
        # Удаляем password2 и теперь с проверкой, если фронты не отправят
        if validated_data['password2']:
            validated_data.pop('password2')
        
        
        # create_user хеширует пароль, create - сохраняет как есть
        user = CustomUser.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],  
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
    #new_password = serializers.CharField(min_length=6, write_only=True)
    confirm_password = serializers.CharField(min_length=8, write_only=True)
    new_password = serializers.CharField(
        min_length=8,
        write_only=True, 
        style={'input_type': 'password'},
        validators=[validate_password_strength] 
    )
    def validate(self, data):
        if ['new_password'] and data['confirm_password']:
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
    
    
# Posts & Photos
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

##########
class PostSerializer(serializers.ModelSerializer):
    """
    Полный сериализатор для поста
    """
    author_username = serializers.CharField(source='author.username', read_only=True)
    author_email = serializers.EmailField(source='author.email', read_only=True)
    photos = PostPhotoSerializer(many=True, read_only=True)
    photo_count = serializers.IntegerField(read_only=True)
    first_photo = serializers.SerializerMethodField()
    rubric_name = serializers.CharField(source='rubric.name', read_only=True)
    
    class Meta:
        model = Post
        fields = [
            'id',                # Номер поста/сообщения
            'title',              # Тема сообщения (заголовок)
            'description',        # Текст сообщения
            'address',            # Адрес события (по ТЗ)
            'latitude',           # Широта (координаты)
            'longitude',          # Долгота (координаты)
            'rubric',             # ID рубрики (для записи)
            'rubric_name',        # Имя рубрики (для отображения)
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
        extra_kwargs = {
            'title': {
                'validators': [validate_title_length]
            },
            'description': {
                'validators': [validate_description_length]
            }
        }
    
    def get_first_photo(self, obj):
        """Возвращает первую фотографию для превью"""
        first = obj.photos.first()
        if first:
            return PostPhotoSerializer(first, context=self.context).data
        return None
    
    def validate_title(self, value):
        """Дополнительная валидация заголовка"""
        # Проверка на пустую строку или только пробелы
        if not value or not value.strip():
            raise serializers.ValidationError("Заголовок не может быть пустым или состоять только из пробелов")
        
        
        validate_title_length(value)
        
        return value.strip()  # Убираем лишние пробелы в начале и конце
    
    def validate_description(self, value):
        """Дополнительная валидация описания"""
        if value:  # Описание может быть пустым
            # Применяем наш валидатор
            validate_description_length(value)
            
            # Убираем лишние пробелы
            value = value.strip()
        
        return value


class PostCreateSerializer(serializers.ModelSerializer):
    """
    Сериализатор для создания поста/сообщения (по ТЗ)
    """
    class Meta:
        model = Post
        fields = ['id', 'title', 'description', 'address', 'latitude', 'longitude', 'rubric', 'status']
        read_only_fields = ['id']
        extra_kwargs = {
            'title': {
                'required': True,
                'validators': [validate_title_length]
            },
            'description': {
                'required': False,
                'allow_blank': True,
                'validators': [validate_description_length]
            },
            'address': {
                'required': False,
                'allow_blank': True
            }
        }
    
    def create(self, validated_data):
        validated_data['author'] = self.context['request'].user
        return super().create(validated_data)
    
    def validate_title(self, value):
        """Валидация заголовка при создании"""
        if not value or not value.strip():
            raise serializers.ValidationError("Заголовок не может быть пустым или состоять только из пробелов")
        
        if len(value.strip()) < 3:
            raise serializers.ValidationError("Заголовок должен содержать минимум 3 символа")
        
        
        validate_title_length(value)
        
        return value.strip()
    
    def validate_description(self, value):
        """Валидация описания при создании"""
        if value:
            if len(value.strip()) < 10:
                raise serializers.ValidationError("Описание должно содержать минимум 10 символов")
            
            
            validate_description_length(value)
            
            return value.strip()
        return value
    
    def validate_status(self, value):
        user = self.context['request'].user
        
        # Доступные статусы для обычных пользователей
        user_allowed_statuses = ['draft', 'check']
        
        # Все доступные статусы
        all_statuses = ['draft', 'published', 'archived', 'check']
        
        if not user.is_superuser and value not in user_allowed_statuses:
            raise serializers.ValidationError(
                f"Обычные пользователи могут выбрать только статусы: {', '.join(user_allowed_statuses)}"
            )
        return value
    
    def validate(self, data):
        """Общая валидация данных"""
        # Проверка координат: если указана одна, должна быть указана и вторая
        lat = data.get('latitude')
        lon = data.get('longitude')
        
        if (lat is not None and lon is None) or (lat is None and lon is not None):
            raise serializers.ValidationError(
                "Должны быть указаны обе координаты: и широта, и долгота"
            )
        
        # Проверка диапазона координат
        if lat is not None and lon is not None:
            if lat < -90 or lat > 90:
                raise serializers.ValidationError({"latitude": "Широта должна быть в диапазоне от -90 до 90"})
            if lon < -180 or lon > 180:
                raise serializers.ValidationError({"longitude": "Долгота должна быть в диапазоне от -180 до 180"})
        
        return data


class PostUpdateSerializer(serializers.ModelSerializer):
    """
    Сериализатор для обновления поста/сообщения
    """
    class Meta:
        model = Post
        fields = ['id', 'title', 'description', 'address', 'latitude', 'longitude', 'rubric', 'status']
        read_only_fields = ['id']
        extra_kwargs = {
            'title': {
                'required': False,
                'validators': [validate_title_length]
            },
            'description': {
                'required': False,
                'allow_blank': True,
                'validators': [validate_description_length]
            }
        }
    
    def validate_title(self, value):
        """Валидация заголовка при обновлении"""
        if value is not None:  # Поле может не передаваться
            if not value.strip():
                raise serializers.ValidationError("Заголовок не может быть пустым или состоять только из пробелов")
            
            if len(value.strip()) < 3:
                raise serializers.ValidationError("Заголовок должен содержать минимум 3 символа")
            
            # Применяем наш валидатор
            validate_title_length(value)
            
            return value.strip()
        return value
    
    def validate_description(self, value):
        """Валидация описания при обновлении"""
        if value is not None:  # Поле может не передаваться
            if value and len(value.strip()) < 10:
                raise serializers.ValidationError("Описание должно содержать минимум 10 символов")
            
            
            if value:
                validate_description_length(value)
                return value.strip()
        return value
    
    def validate_status(self, value):
        user = self.context['request'].user
        
        # Доступные статусы для обычных пользователей
        user_allowed_statuses = ['draft', 'check']
        
        # Проверка для обычных пользователей
        if not user.is_superuser and value not in user_allowed_statuses:
            raise serializers.ValidationError(
                f"Обычные пользователи могут выбрать только статусы: {', '.join(user_allowed_statuses)}"
            )
        
        return value
    
    def validate(self, data):
        user = self.context['request'].user
        instance = self.instance
        
        if instance and not user.is_superuser:
            if 'status' in data:
                new_status = data['status']
                
                # Проверяем, что новый статус в списке разрешенных
                if new_status not in ['draft', 'check']:
                    raise serializers.ValidationError({
                        'status': f'Обычные пользователи могут выбрать только статусы: draft, check'
                    })
        
        
        lat = data.get('latitude')
        lon = data.get('longitude')
        
        if (lat is not None and lon is None) or (lat is None and lon is not None):
            raise serializers.ValidationError(
                "Должны быть указаны обе координаты: и широта, и долгота"
            )
        
        if lat is not None and lon is not None:
            if lat < -90 or lat > 90:
                raise serializers.ValidationError({"latitude": "Широта должна быть в диапазоне от -90 до 90"})
            if lon < -180 or lon > 180:
                raise serializers.ValidationError({"longitude": "Долгота должна быть в диапазоне от -180 до 180"})
        
        return data
####
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
    rubric_name = serializers.CharField(source='rubric.name', read_only=True)
    
    class Meta:
        model = Post
        fields = [
            'id', 'title', 'address', 'latitude', 'longitude',
            'rubric_name',
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