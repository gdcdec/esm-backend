# api/validators.py
from django.core.exceptions import ValidationError
import os
from PIL import Image
import io
import re
from django.utils.translation import gettext_lazy as _

def validate_image_size(file):
    """
    Проверка размера файла (макс ? МБ)
    """
    max_size_mb = 10
    max_size_bytes = max_size_mb * 1024 * 1024
    
    if file.size > max_size_bytes:
        raise ValidationError(
            f"Файл слишком большой. Максимальный размер: {max_size_mb} МБ. "
            f"Текущий размер: {file.size / (1024 * 1024):.1f} МБ"
        )

def validate_image_extension(file):
    """
    Проверка расширения файла
    """
    # Получаем расширение файла
    ext = os.path.splitext(file.name)[1].lower()
    
    # Разрешенные расширения
    valid_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp']
    
    if ext not in valid_extensions:
        raise ValidationError(
            f"Неподдерживаемый формат файла. Разрешены: {', '.join(valid_extensions)}"
        )

def validate_image_content(file):
    """
    Проверка, что файл действительно является изображением
    """
    try:
        # Пытаемся открыть файл как изображение
        image = Image.open(file)
        image.verify()  # Проверяем целостность
        
        # Сбрасываем указатель файла в начало
        file.seek(0)
        
    except Exception as e:
        raise ValidationError(f"Файл не является корректным изображением: {str(e)}")

def validate_image_dimensions(file, max_width=5000, max_height=5000):
    """
    Проверка размеров изображения
    """
    try:
        image = Image.open(file)
        width, height = image.size
        
        if width > max_width or height > max_height:
            raise ValidationError(
                f"Изображение слишком большое. Максимальные размеры: "
                f"{max_width}x{max_height}. "
                f"Текущие размеры: {width}x{height}"
            )
        
        # Сбрасываем указатель файла в начало
        file.seek(0)
        
    except Exception as e:
        raise ValidationError(f"Не удалось проверить размеры изображения: {str(e)}")

# Комбинированный валидатор для удобства
def validate_image(file):
    """
    Полная проверка изображения
    """
    validate_image_extension(file)
    validate_image_size(file)
    validate_image_content(file)
    validate_image_dimensions(file)

def validate_username(value):
    """
    Валидация логина:
    - только латинские буквы, цифры, символы «-», «_», «.»
    - запрещены «@», пробелы
    - не может начинаться или заканчиваться точкой
    """
    if not value:
        raise ValidationError(_('Логин не может быть пустым.'))
    
    # Проверка на недопустимые символы
    if not re.match(r'^[a-zA-Z0-9._-]+$', value):
        raise ValidationError(
            _('Логин может содержать только латинские буквы, цифры и символы . _ -')
        )
    
    # Проверка на запрещенные символы
    if '@' in value:
        raise ValidationError(_('Логин не может содержать символ @'))
    
    if ' ' in value:
        raise ValidationError(_('Логин не может содержать пробелы'))
    
    # Проверка на начало или конец с точкой
    if value.startswith('.'):
        raise ValidationError(_('Логин не может начинаться с точки'))
    
    if value.endswith('.'):
        raise ValidationError(_('Логин не может заканчиваться точкой'))
    
    # Дополнительные проверки
    if len(value) < 3:
        raise ValidationError(_('Логин должен содержать минимум 3 символа'))
    
    if len(value) > 30:
        raise ValidationError(_('Логин не может превышать 30 символов'))


def validate_password_strength(value):
    """
    Валидация пароля:
    - заглавные и строчные латинские буквы (A–Z, a–z)
    - цифры (0–9)
    - спецсимволы !"#$%&'()*+,-./:;<=>?@[\]^_`{|}~ и пробел
    - минимум 8 символов
    """
    if not value:
        raise ValidationError(_('Пароль не может быть пустым.'))
    
    # Проверка длины
    if len(value) < 8:
        raise ValidationError(_('Пароль должен содержать минимум 8 символов'))
    
    if len(value) > 32:
        raise ValidationError(_('Пароль не может превышать 32 символов'))
    
    # Проверка на допустимые символы (латиница, цифры, спецсимволы и пробел)
    allowed_chars = r'^[A-Za-z0-9\s!"#$%&\'()*+,\-./:;<=>?@\[\\\]^_`{|}~]+$'
    if not re.match(allowed_chars, value):
        raise ValidationError(
            _('Пароль может содержать только латинские буквы, цифры, спецсимволы и пробел')
        )
    
    # Проверка наличия хотя бы одной заглавной буквы
    if not re.search(r'[A-Z]', value):
        raise ValidationError(_('Пароль должен содержать хотя бы одну заглавную букву'))
    
    # Проверка наличия хотя бы одной строчной буквы
    if not re.search(r'[a-z]', value):
        raise ValidationError(_('Пароль должен содержать хотя бы одну строчную букву'))
    
    # Проверка наличия хотя бы одной цифры
    if not re.search(r'[0-9]', value):
        raise ValidationError(_('Пароль должен содержать хотя бы одну цифру'))
    
    # Проверка наличия хотя бы одного спецсимвола или пробела
    if not re.search(r'[^A-Za-z0-9]', value):
        raise ValidationError(_('Пароль должен содержать хотя бы один спецсимвол или пробел'))


def validate_email_strict(value):
    """
    Валидация email:
    - латинские буквы, цифры
    - спецсимволы !#$%&'*+-/=?^_`{|}~ и точка
    - точка не может быть первым/последним символом
    - точка не может встречаться подряд
    - должен содержать @ и домен
    """
    if not value:
        raise ValidationError(_('Email не может быть пустым.'))
    
    # Базовая проверка формата email
    if '@' not in value:
        raise ValidationError(_('Email должен содержать символ @'))
    
    local_part, domain = value.rsplit('@', 1)
    
    # Проверка local-part
    if not local_part:
        raise ValidationError(_('Локальная часть email не может быть пустой'))
    
    # Проверка на недопустимые символы в local-part
    allowed_local = r'^[a-zA-Z0-9!#$%&\'*+\-/=?^_`{|}~.]+$'
    if not re.match(allowed_local, local_part):
        raise ValidationError(
            _('Локальная часть email содержит недопустимые символы')
        )
    
    # Проверка на точки в local-part
    if local_part.startswith('.'):
        raise ValidationError(_('Email не может начинаться с точки'))
    
    if local_part.endswith('.'):
        raise ValidationError(_('Email не может заканчиваться точкой'))
    
    if '..' in local_part:
        raise ValidationError(_('Email не может содержать две точки подряд'))
    
    # Проверка домена
    if not domain:
        raise ValidationError(_('Домен email не может быть пустым'))
    
    if '.' not in domain:
        raise ValidationError(_('Домен должен содержать точку'))
    
    if len(domain) < 3:
        raise ValidationError(_('Домен слишком короткий'))
    
    return value


def validate_phone_number(value):
    """
    Валидация телефона:
    - формат +7 XXX XXX XX XX
    - ввод только цифр (форматирование на фронте)
    """
    if not value:
        raise ValidationError(_('Телефон не может быть пустым.'))
    
    # Удаляем все нецифровые символы для проверки
    digits_only = re.sub(r'\D', '', value)
    
    # Проверка что остались только цифры
    if not digits_only.isdigit():
        raise ValidationError(_('Телефон должен содержать только цифры'))
    
    # Проверка длины (11 цифр для российского номера)
    if len(digits_only) != 11:
        raise ValidationError(_('Телефон должен содержать 11 цифр (включая код страны)'))
    
    # Проверка что начинается с 7
    if not digits_only.startswith('7'):
        raise ValidationError(_('Телефон должен начинаться с 7 (код России)'))
    
    # Дополнительная проверка формата если нужно
    
    
    # Форматируем для хранения
    formatted = f"+{digits_only[0]}{digits_only[1:4]}{digits_only[4:7]}{digits_only[7:9]}{digits_only[9:11]}"
    
    return formatted


def validate_cyrillic_name(value, field_name="Имя"):
    """
    Общая валидация для имени, фамилии, отчества:
    - только кириллица
    - запрещены цифры, латиница и спецсимволы
    - дефис разрешен только в фамилии
    """
    if not value:
        if field_name == "Отчество":  # Отчество необязательно
            return value
        raise ValidationError(_(f'{field_name} не может быть пустым.'))
    
    # Проверка на длину
    if len(value) < 2:
        raise ValidationError(_(f'{field_name} должно содержать минимум 2 символа'))
    
    if len(value) > 50:
        raise ValidationError(_(f'{field_name} не может превышать 50 символов'))
    
    # Проверка на кириллицу, пробелы и дефис (для фамилии)
    if field_name == "Фамилия":
        # Для фамилии разрешаем дефис
        if not re.match(r'^[а-яА-ЯёЁ\s-]+$', value):
            raise ValidationError(_(f'{field_name} может содержать только кириллицу, пробел и дефис'))
        
        # Проверка на корректное использование дефиса
        if '--' in value:
            raise ValidationError(_(f'{field_name} не может содержать два дефиса подряд'))
        
        if value.startswith('-') or value.endswith('-'):
            raise ValidationError(_(f'{field_name} не может начинаться или заканчиваться дефисом'))
    else:
        # Для имени и отчества дефис не разрешен
        if not re.match(r'^[а-яА-ЯёЁ\s]+$', value):
            raise ValidationError(_(f'{field_name} может содержать только кириллицу и пробел'))
    
    # Запрет на латиницу и цифры
    if re.search(r'[a-zA-Z0-9]', value):
        raise ValidationError(_(f'{field_name} не может содержать латиницу или цифры'))
    
    # Если надо тут доабить ещё
    
    return value


def validate_first_name(value):
    """Валидация имени"""
    return validate_cyrillic_name(value, "Имя")


def validate_last_name(value):
    """Валидация фамилии"""
    return validate_cyrillic_name(value, "Фамилия")


def validate_patronymic(value):
    """Валидация отчества (необязательное)"""
    if not value:  # Пустое значение разрешено
        return value
    return validate_cyrillic_name(value, "Отчество")


def validate_street(value):
    """
    Валидация улицы:
    - цифры, кириллица, дефис, дробь
    - пробелы разрешены
    """
    if not value:
        raise ValidationError(_('Улица не может быть пустой.'))
    
    if len(value) > 100:
        raise ValidationError(_('Название улицы не может превышать 100 символов'))
    
    # Разрешены: кириллица, цифры, пробелы, дефис, дробь, точка
    if not re.match(r'^[а-яА-ЯёЁ0-9\s\-/.,]+$', value):
        raise ValidationError(
            _('Улица может содержать только кириллицу, цифры, пробелы, дефис, дробь и точку')
        )
    
    return value


def validate_house(value):
    """
    Валидация дома:
    - цифры, кириллица, дефис, дробь
    - буквы только кириллица
    """
    if not value:
        raise ValidationError(_('Номер дома не может быть пустым.'))
    
    if len(value) > 20:
        raise ValidationError(_('Номер дома не может превышать 20 символов'))
    
    # Разрешены: кириллица, цифры, дефис, дробь
    if not re.match(r'^[а-яА-ЯёЁ0-9\-/]+$', value):
        raise ValidationError(
            _('Номер дома может содержать только кириллицу, цифры, дефис и дробь')
        )
    
    # Проверка на некорректное использование дефиса
    if value.startswith('-') or value.endswith('-'):
        raise ValidationError(_('Номер дома не может начинаться или заканчиваться дефисом'))
    
    return value


def validate_apartment(value):
    """
    Валидация квартиры (необязательно):
    - цифры и кириллица
    - пробелы не разрешены
    """
    if not value:  # Пустое значение разрешено
        return value
    
    if len(value) > 10:
        raise ValidationError(_('Номер квартиры не может превышать 10 символов'))
    
    if not re.match(r'^[а-яА-ЯёЁ0-9]+$', value):
        raise ValidationError(
            _('Номер квартиры может содержать только кириллицу и цифры')
        )
    
    return value


def validate_city(value):# НЕ ЗАКОНЧЕНО
    """
    Валидация города:
    - для MVP предзаполнен значением «Самара»
    """
    if not value:
        return "Самара"  # Значение по умолчанию
    
    # Проверка что город из списка разрешенных (для MVP)
    allowed_cities = ['Самара', 'Москва', 'Санкт-Петербург', 'Владиосток']  # Расширяйте по необходимости
    
    if value not in allowed_cities:
        # Для MVP можно автоматически устанавливать Самару
        #return "Самара"
        return value
    
    return value

def validate_title_length(value):
    """
    Валидация длины заголовка поста
    """
    if not value:
        raise ValidationError('Заголовок не может быть пустым.')
    
    # Убираем пробелы для проверки реальной длины
    stripped_value = value.strip() if isinstance(value, str) else value
    
    if len(stripped_value) < 3:
        raise ValidationError('Заголовок должен содержать минимум 3 символа.')
    
    if len(stripped_value) > 200:
        raise ValidationError('Заголовок не может превышать 200 символов.')
    
    return value


def validate_description_length(value):
    """
    Валидация длины описания поста
    """
    if not value:  # Описание может быть пустым
        raise ValidationError('Описание не может быть пустым.')
        #return value
    
    # Убираем пробелы для проверки реальной длины
    stripped_value = value.strip() if isinstance(value, str) else value
    
    if len(stripped_value) < 10:
        raise ValidationError('Описание должно содержать минимум 10 символов.')
    
    # Максимальная длина для TextField (можно настроить)
    if len(stripped_value) > 5000:
        raise ValidationError('Описание не может превышать 5000 символов.')
    
    return value