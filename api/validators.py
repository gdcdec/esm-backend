# api/validators.py
from django.core.exceptions import ValidationError
import os
from PIL import Image
import io

def validate_image_size(file):
    """
    Проверка размера файла (макс 5 МБ)
    """
    max_size_mb = 5
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