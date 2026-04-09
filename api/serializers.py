from rest_framework import serializers
from .models import Rubric
from .models import CustomUser
from .models import PasswordReset
from .models import Post, PostPhoto
from .models import Notification
from django.contrib.auth import get_user_model
from .validators import (
    validate_username, validate_password_strength, validate_email_strict,
    validate_phone_number, validate_first_name, validate_last_name,
    validate_patronymic, validate_street, validate_house, validate_apartment,
    validate_city, validate_title_length, validate_description_length
)

User = get_user_model()

def _extract_error_message(e):
    if hasattr(e, 'message'):
        return e.message
    if hasattr(e, 'messages') and e.messages:
        return e.messages[0]
    return str(e)

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
    """
    Сериализатор для регистрации пользователя
    """
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
    
    class Meta:
        model = CustomUser
        fields = [
            'username', 'email', 'password', 'password2',
            'first_name', 'last_name', 'patronymic',
            'phone_number', 'city', 'street', 'house', 'apartment'
        ]
        extra_kwargs = {
            'email': {'required': True},
            'username': {'required': True},
            'first_name': {'required': False, 'allow_blank': True},
            'last_name': {'required': False, 'allow_blank': True},
            'patronymic': {'required': False, 'allow_blank': True},
            'phone_number': {'required': False, 'allow_blank': True},
            'city': {'required': False, 'allow_blank': True},
            'street': {'required': False, 'allow_blank': True},
            'house': {'required': False, 'allow_blank': True},
            'apartment': {'required': False, 'allow_blank': True},
        }
    
    def validate_username(self, value):
        """Валидация username"""
        # Применяем валидатор
        try:
            validate_username(value)
        except Exception as e:
            raise serializers.ValidationError(_extract_error_message(e))
        
        # Проверка уникальности
        if CustomUser.objects.filter(username=value).exists():
            raise serializers.ValidationError("Пользователь с таким логином уже существует")
        
        return value
    
    def validate_email(self, value):
        """Валидация email"""
        # Применяем валидатор
        try:
            validate_email_strict(value)
        except Exception as e:
            raise serializers.ValidationError(_extract_error_message(e))
        
        # Проверка уникальности
        if CustomUser.objects.filter(email=value).exists():
            raise serializers.ValidationError("Пользователь с таким email уже существует")
        
        return value
    
    def validate_first_name(self, value):
        """Валидация имени"""
        if value:
            try:
                validate_first_name(value)
            except Exception as e:
                raise serializers.ValidationError(_extract_error_message(e))
        return value
    
    def validate_last_name(self, value):
        """Валидация фамилии"""
        if value:
            try:
                validate_last_name(value)
            except Exception as e:
                raise serializers.ValidationError(_extract_error_message(e))
        return value
    
    def validate_patronymic(self, value):
        """Валидация отчества"""
        if value:
            try:
                validate_patronymic(value)
            except Exception as e:
                raise serializers.ValidationError(_extract_error_message(e))
        return value
    
    def validate_phone_number(self, value):
        """Валидация телефона"""
        if value:
            try:
                return validate_phone_number(value)
            except Exception as e:
                raise serializers.ValidationError(_extract_error_message(e))
        return value
    
    def validate_city(self, value):
        """Валидация города"""
        if value:
            try:
                validate_city(value)
            except Exception as e:
                raise serializers.ValidationError(_extract_error_message(e))
            return value
        return "Самара"  # Значение по умолчанию
    
    def validate_street(self, value):
        """Валидация улицы"""
        if value:
            try:
                validate_street(value)
            except Exception as e:
                raise serializers.ValidationError(_extract_error_message(e))
        return value
    
    def validate_house(self, value):
        """Валидация дома"""
        if value:
            try:
                validate_house(value)
            except Exception as e:
                raise serializers.ValidationError(_extract_error_message(e))
        return value
    
    def validate_apartment(self, value):
        """Валидация квартиры"""
        if value:
            try:
                validate_apartment(value)
            except Exception as e:
                raise serializers.ValidationError(_extract_error_message(e))
        return value
    
    def validate(self, data):
        """Общая валидация"""
        # Проверка совпадения паролей
        password = data.get('password')
        password2 = data.get('password2')
        
        if password and password2 and password != password2:
            raise serializers.ValidationError({"password2": "Пароли не совпадают"})
        
        return data
    
    def create(self, validated_data):
        """Создание пользователя"""
        # Удаляем password2
        validated_data.pop('password2', None)
        
        # Создаем пользователя
        user = CustomUser.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            patronymic=validated_data.get('patronymic', ''),
            phone_number=validated_data.get('phone_number', ''),
            city=validated_data.get('city', 'Самара'),
            street=validated_data.get('street', ''),
            house=validated_data.get('house', ''),
            apartment=validated_data.get('apartment', '')
        )
        
        return user


class UserUpdateSerializer(serializers.ModelSerializer):
    """
    Сериализатор для обновления данных пользователя с валидацией
    """
    class Meta:
        model = CustomUser
        fields = [
            'first_name', 'last_name', 'patronymic',
            'email', 'phone_number', 'city', 'street',
            'house', 'apartment', 'birth_date'
        ]
        extra_kwargs = {
            'first_name': {'required': False, 'allow_blank': True},
            'last_name': {'required': False, 'allow_blank': True},
            'patronymic': {'required': False, 'allow_blank': True},
            'email': {'required': False},
            'phone_number': {'required': False, 'allow_blank': True},
            'city': {'required': False, 'allow_blank': True},
            'street': {'required': False, 'allow_blank': True},
            'house': {'required': False, 'allow_blank': True},
            'apartment': {'required': False, 'allow_blank': True},
            'birth_date': {'required': False, 'allow_null': True},
        }
    
    def validate_first_name(self, value):
        """Валидация имени"""
        if value:
            try:
                validate_first_name(value)
            except Exception as e:
                raise serializers.ValidationError(_extract_error_message(e))
        return value
    
    def validate_last_name(self, value):
        """Валидация фамилии"""
        if value:
            try:
                validate_last_name(value)
            except Exception as e:
                raise serializers.ValidationError(_extract_error_message(e))
        return value
    
    def validate_patronymic(self, value):
        """Валидация отчества"""
        if value:
            try:
                validate_patronymic(value)
            except Exception as e:
                raise serializers.ValidationError(_extract_error_message(e))
        return value
    
    def validate_email(self, value):
        """Валидация email"""
        if not value:
            return value
        
        # Применяем валидатор формата
        try:
            validate_email_strict(value)
        except Exception as e:
            raise serializers.ValidationError(_extract_error_message(e))
        
        # Проверка уникальности email
        user = self.context['request'].user
        if CustomUser.objects.filter(email=value).exclude(id=user.id).exists():
            raise serializers.ValidationError("Этот email уже используется другим пользователем")
        
        return value
    
    def validate_phone_number(self, value):
        """Валидация телефона"""
        if value:
            try:
                return validate_phone_number(value)
            except Exception as e:
                raise serializers.ValidationError(_extract_error_message(e))
        return value
    
    def validate_city(self, value):
        """Валидация города"""
        if value:
            try:
                validate_city(value)
            except Exception as e:
                raise serializers.ValidationError(_extract_error_message(e))
            return value
        return "Самара"  # Значение по умолчанию
    
    def validate_street(self, value):
        """Валидация улицы"""
        if value:
            try:
                validate_street(value)
            except Exception as e:
                raise serializers.ValidationError(_extract_error_message(e))
        return value
    
    def validate_house(self, value):
        """Валидация дома"""
        if value:
            try:
                validate_house(value)
            except Exception as e:
                raise serializers.ValidationError(_extract_error_message(e))
        return value
    
    def validate_apartment(self, value):
        """Валидация квартиры"""
        if value:
            try:
                validate_apartment(value)
            except Exception as e:
                raise serializers.ValidationError(_extract_error_message(e))
        return value
    
    def validate_birth_date(self, value):
        """Валидация даты рождения"""
        if value:
            # Здесь можно добавить дополнительную валидацию
            # Например, проверка что дата не в будущем
            from django.utils import timezone
            if value > timezone.now().date():
                raise serializers.ValidationError("Дата рождения не может быть в будущем")
        return value
    
    def update(self, instance, validated_data):
        """
        Обновление только переданных полей
        """
        for attr, value in validated_data.items():
            if value is not None:  # Обновляем только переданные поля
                setattr(instance, attr, value)
        instance.save()
        return instance
class UserDetailSerializer(serializers.ModelSerializer):
    """
    Сериализатор для вывода данных пользователя
    """
    class Meta:
        model = CustomUser
        fields = [
            'id', 'username', 'first_name', 'last_name', 'patronymic',
            'email', 'phone_number', 'city', 'street',
            'house', 'apartment', 'birth_date', 'date_joined'
        ]
        read_only_fields = ['id', 'username', 'date_joined']


class CurrentUserUpdateSerializer(UserUpdateSerializer):
    """
    Сериализатор для обновления текущего пользователя
    """
    class Meta(UserUpdateSerializer.Meta):
        pass
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

# Уведомления для пользователя
class NotificationSerializer(serializers.ModelSerializer):
    """Сериализатор для уведомлений"""
    
    notification_type_display = serializers.CharField(
        source='get_notification_type_display',
        read_only=True
    )
    
    class Meta:
        model = Notification
        fields = [
            'id',
            'user',
            'subject',
            'message',
            'is_read',
            'notification_type',
            'notification_type_display',
            'created_at',
            'read_at',
            'link',
            'metadata'
        ]
        read_only_fields = ['id', 'created_at', 'read_at']


class NotificationMarkReadSerializer(serializers.Serializer):
    """Сериализатор для отметки уведомлений как прочитанных"""
    
    notification_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        help_text="Список ID уведомлений для отметки. Если не указано - отметить все"
    )
    mark_all = serializers.BooleanField(
        default=False,
        help_text="Отметить все уведомления как прочитанные"
    )

# Посты и фотки и тп
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
            },
            'description': {
                'required': True,  # Делаем description обязательным
                'allow_blank': False,  # Запрещаем пустые значения
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
        # Проверка на пустоту
        if not value or not value.strip():
            raise serializers.ValidationError("Заголовок не может быть пустым или состоять только из пробелов")
        
        # Очищаем от пробелов
        cleaned_title = value.strip()
        
        # Проверка минимальной длины
        if len(cleaned_title) < 3:
            raise serializers.ValidationError("Заголовок должен содержать минимум 3 символа")
        
        # Используем существующий валидатор для проверки длины
        try:
            validate_title_length(cleaned_title)
        except Exception as e:
            raise serializers.ValidationError(_extract_error_message(e))
        
        return cleaned_title
    
    def validate_description(self, value):
        """Валидация описания при создании"""
        # Проверка что поле существует и не пустое
        if not value:
            raise serializers.ValidationError("Описание обязательно для заполнения")
        
        if not value.strip():
            raise serializers.ValidationError("Описание не может состоять только из пробелов")
        
        cleaned_description = value.strip()
        
        # Проверка минимальной длины
        if len(cleaned_description) < 10:
            raise serializers.ValidationError("Описание должно содержать минимум 10 символов")
        
        # Проверка максимальной длины через валидатор
        try:
            validate_description_length(cleaned_description)
        except Exception as e:
            raise serializers.ValidationError(_extract_error_message(e))
        
        return cleaned_description
    
    def validate_status(self, value):
        """Валидация статуса при создании"""
        user = self.context['request'].user
        
        # Доступные статусы для обычных пользователей
        user_allowed_statuses = ['draft', 'check']
        
        if not user.is_superuser:
            if value not in user_allowed_statuses:
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
    PUT - полное обновление (все поля обязательны)
    PATCH - частичное обновление (только переданные поля)
    """
    class Meta:
        model = Post
        fields = [
            'id', 'title', 'description', 'address', 
            'latitude', 'longitude', 'rubric', 'status'
        ]
        read_only_fields = ['id']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get('request')
        
        # Для PUT запроса делаем все поля обязательными
        if request and request.method == 'PUT':
            for field in self.fields.values():
                field.required = True
                if hasattr(field, 'allow_blank'):
                    field.allow_blank = False
                if hasattr(field, 'allow_null'):
                    field.allow_null = False
    
    def validate_title(self, value):
        """Валидация заголовка"""
        if value is not None:
            # Проверка на пустоту
            if isinstance(value, str) and not value.strip():
                raise serializers.ValidationError("Заголовок не может быть пустым")
            
            cleaned_title = value.strip() if isinstance(value, str) else value
            
            if len(cleaned_title) < 3:
                raise serializers.ValidationError("Заголовок должен содержать минимум 3 символа")
            
            try:
                validate_title_length(cleaned_title)
            except Exception as e:
                raise serializers.ValidationError(_extract_error_message(e))
            
            return cleaned_title
        
        # Если значение None и это PUT запрос - ошибка
        request = self.context.get('request')
        if request and request.method == 'PUT':
            raise serializers.ValidationError("Заголовок обязателен")
        
        return value
    
    def validate_description(self, value):
        """Валидация описания"""
        if value is not None:
            if isinstance(value, str) and not value.strip():
                raise serializers.ValidationError("Описание не может быть пустым")
            
            cleaned_description = value.strip() if isinstance(value, str) else value
            
            if len(cleaned_description) < 10:
                raise serializers.ValidationError("Описание должно содержать минимум 10 символов")
            
            try:
                validate_description_length(cleaned_description)
            except Exception as e:
                raise serializers.ValidationError(_extract_error_message(e))
            
            return cleaned_description
        
        # Если значение None и это PUT запрос - ошибка
        request = self.context.get('request')
        if request and request.method == 'PUT':
            raise serializers.ValidationError("Описание обязательно")
        
        return value
    
    def validate_address(self, value):
        """Валидация адреса"""
        if value is not None:
            if isinstance(value, str) and not value.strip():
                return None
            return value.strip() if isinstance(value, str) else value
        return value
    
    def validate_latitude(self, value):
        """Валидация широты"""
        if value is not None:
            if value == '' or value is None:
                return None
            
            try:
                value = float(value)
                if value < -90 or value > 90:
                    raise serializers.ValidationError("Широта должна быть в диапазоне от -90 до 90")
            except (TypeError, ValueError):
                raise serializers.ValidationError("Некорректное значение широты")
            
            return value
        return value
    
    def validate_longitude(self, value):
        """Валидация долготы"""
        if value is not None:
            if value == '' or value is None:
                return None
            
            try:
                value = float(value)
                if value < -180 or value > 180:
                    raise serializers.ValidationError("Долгота должна быть в диапазоне от -180 до 180")
            except (TypeError, ValueError):
                raise serializers.ValidationError("Некорректное значение долготы")
            
            return value
        return value
    
    def validate_rubric(self, value):
        """Валидация рубрики"""
        if value is not None:
            if value == '' or value is None:
                return None
            return value
        return value
    
    def validate_status(self, value):
        """Валидация статуса"""
        if value is not None:
            user = self.context['request'].user
            
            # Доступные статусы для обычных пользователей
            user_allowed_statuses = ['draft', 'check']
            
            # Проверка для обычных пользователей
            if not user.is_superuser:
                if value not in user_allowed_statuses:
                    raise serializers.ValidationError(
                        f"Обычные пользователи могут выбрать только статусы: {', '.join(user_allowed_statuses)}"
                    )
            
            return value
        
        # Если значение None и это PUT запрос - ошибка
        request = self.context.get('request')
        if request and request.method == 'PUT':
            raise serializers.ValidationError("Статус обязателен")
        
        return value
    
    def validate(self, data):
        """Общая валидация данных"""
        user = self.context['request'].user
        instance = self.instance
        request = self.context.get('request')
        
        # Проверка для обычных пользователей
        if instance and not user.is_superuser:
            # Проверяем, пытается ли пользователь изменить опубликованный пост
            if instance.status == 'published':
                # Проверяем, какие поля переданы в запросе
                fields_to_check = ['title', 'description', 'address', 'latitude', 'longitude']
                for field in fields_to_check:
                    if field in self.initial_data:
                        raise serializers.ValidationError(
                            f"Нельзя редактировать опубликованный пост. Поле '{field}' не может быть изменено"
                        )
        
        # Для PUT запроса - проверяем координаты
        if request and request.method == 'PUT':
            lat = data.get('latitude')
            lon = data.get('longitude')
            
            # Если указана одна координата, должна быть указана и вторая
            if (lat is not None and lon is None) or (lat is None and lon is not None):
                raise serializers.ValidationError(
                    "Должны быть указаны обе координаты: и широта, и долгота"
                )
        
        # Для PATCH запроса - проверка координат с учетом существующих
        else:
            lat_in_request = 'latitude' in self.initial_data
            lon_in_request = 'longitude' in self.initial_data
            lat = data.get('latitude')
            lon = data.get('longitude')
            
            if lat_in_request and not lon_in_request:
                if instance.longitude is None and lat is not None:
                    raise serializers.ValidationError(
                        "Нельзя установить широту без долготы"
                    )
            elif not lat_in_request and lon_in_request:
                if instance.latitude is None and lon is not None:
                    raise serializers.ValidationError(
                        "Нельзя установить долготу без широты"
                    )
        
        return data
    
    def update(self, instance, validated_data):
        """
        Обновление поста
        PUT - обновляем все поля (то, что не передано - очищаем)
        PATCH - обновляем только переданные поля
        """
        request = self.context.get('request')
        
        if request and request.method == 'PUT':
            # Для PUT - обновляем все поля
            # Поля, которые не попали в validated_data, нужно очистить
            for field in self.fields:
                if field in validated_data:
                    setattr(instance, field, validated_data[field])
                else:
                    # Очищаем поле (устанавливаем значение по умолчанию)
                    if field in ['title', 'description', 'status']:
                        # Обязательные поля - оставляем как есть, но если они не переданы - ошибка
                        # Это уже проверено в валидации
                        pass
                    elif field in ['address', 'rubric']:
                        setattr(instance, field, None)
                    elif field in ['latitude', 'longitude']:
                        setattr(instance, field, None)
        else:
            # Для PATCH - обновляем только переданные поля
            for attr, value in validated_data.items():
                setattr(instance, attr, value)
        
        instance.save()
        return instance
    
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
            'rubric_name', 'status',
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
