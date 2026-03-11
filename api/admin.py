from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Rubric, CustomUser, Post, PostPhoto
from django.utils.html import format_html
# Register your models here.


class PostPhotoInline(admin.TabularInline):
    """
    Инлайн для отображения фотографий внутри поста
    """
    model = PostPhoto
    extra = 1  # Количество пустых форм для новых фото
    fields = ['photo', 'caption', 'order', 'photo_preview']
    readonly_fields = ['photo_preview']
    
    def photo_preview(self, obj):
        """Превью фотографии в админке"""
        if obj.photo:
            return format_html(
                '<img src="{}" style="max-height: 100px; max-width: 100px;" />',
                obj.photo.url
            )
        return "Нет фото"
    photo_preview.short_description = "Превью"


@admin.register(Rubric)
class RubricAdmin(admin.ModelAdmin):
    list_display = ('name', 'counter', 'posts_count', 'photo_preview')
    search_fields = ('name',)
    list_filter = ('counter',)
    readonly_fields = ('counter', 'posts_count', 'photo_preview')
    
    def posts_count(self, obj):
        return obj.posts.count()
    posts_count.short_description = "Постов"
    
    def photo_preview(self, obj):
        if obj.photo:
            return format_html('<img src="{}" style="max-height: 50px;" />', obj.photo.url)
        return "Нет фото"
    photo_preview.short_description = "Фото"


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    """
    Админка для постов
    """
    list_display = [
        'id', 'title_preview', 'author', 'rubric', 
        'status', 'created_at', 'photo_count_display', 'has_photos'
    ]
    list_display_links = ['id', 'title_preview']
    list_filter = ['status', 'rubric', 'is_deleted', 'created_at']
    search_fields = ['title', 'description', 'address']
    readonly_fields = [
        'created_at', 'updated_at', 'published_at', 
        'photo_count', 'first_photo_preview', 'all_photos_preview'
    ]
    fieldsets = (
        ('Основная информация', {
            'fields': ('title', 'description', 'author', 'rubric')
        }),
        ('Статус и даты', {
            'fields': ('status', 'is_deleted', 'created_at', 'updated_at', 'published_at'),
            'classes': ('collapse',)
        }),
        ('Адрес и координаты', {
            'fields': ('address', 'latitude', 'longitude'),
            'classes': ('collapse',)
        }),
        ('Фотографии', {
            'fields': ('photo_count', 'first_photo_preview', 'all_photos_preview'),
            'classes': ('collapse',)
        }),
    )
    
    # Инлайн для фотографий
    inlines = [PostPhotoInline]
    
    def title_preview(self, obj):
        """Превью заголовка с обрезанием - защищено от None"""
        # Проверяем, что obj существует
        if not obj:
            return "[Нет объекта]"
        
        # Проверяем title на None
        if obj.title is None:
            return "[Без заголовка]"
        
        # Проверяем, что title - строка
        if not isinstance(obj.title, str):
            try:
                title_str = str(obj.title)
            except:
                return "[Нестроковый заголовок]"
        else:
            title_str = obj.title
        
        # Если пустая строка
        if title_str == "":
            return "[Пустой заголовок]"
        
        # Обрезаем если длинный
        if len(title_str) > 50:
            return f"{title_str[:50]}..."
        return title_str
    
    title_preview.short_description = "Заголовок"
    
    # Также добавьте защиту в search_fields, чтобы поиск по None не падал
    def get_search_results(self, request, queryset, search_term):
        queryset, use_distinct = super().get_search_results(request, queryset, search_term)
        # Дополнительная защита от поиска по None
        return queryset, use_distinct
    
    def photo_count_display(self, obj):
        """Отображение количества фото"""
        try:
            count = obj.photo_count
            if count:
                return format_html(
                    '<b style="color: green;">{} фото</b>',
                    count
                )
        except:
            pass
        return '<span style="color: gray;">нет фото</span>'
    photo_count_display.short_description = "Фото"
    
    def has_photos(self, obj):
        """Есть ли фото"""
        try:
            return obj.photos.exists()
        except:
            return False
    has_photos.boolean = True
    has_photos.short_description = "Есть фото"
    
    def first_photo_preview(self, obj):
        """Превью первого фото с защитой от ошибок"""
        try:
            # Проверяем obj
            if not obj:
                return "Нет объекта"
            
            first = obj.first_photo
            if first and first.photo:
                return format_html(
                    '<img src="{}" style="max-height: 200px; max-width: 200px;" />',
                    first.photo.url
                )
        except Exception as e:
            # Логируем ошибку для отладки
            print(f"Error in first_photo_preview for post {getattr(obj, 'id', 'None')}: {e}")
        return "Нет фотографий или ошибка"
    first_photo_preview.short_description = "Главное фото"
    
    def all_photos_preview(self, obj):
        """Превью всех фото с защитой от ошибок"""
        try:
            # Проверяем obj
            if not obj:
                return "Нет объекта"
            
            photos = obj.photos.all()
            if not photos:
                return "Нет фотографий"
            
            html = '<div style="display: flex; flex-wrap: wrap; gap: 10px;">'
            for photo in photos:
                try:
                    if photo and photo.photo:
                        # Безопасное получение order и caption
                        order = photo.order if photo.order is not None else '?'
                        caption = photo.caption or 'без подписи'
                        
                        html += format_html(
                            '<div style="border: 1px solid #ddd; padding: 5px;">'
                            '<img src="{}" style="max-height: 100px; max-width: 100px;" /><br/>'
                            '<small>{}: {}</small>'
                            '</div>',
                            photo.photo.url,
                            order,
                            caption
                        )
                except Exception as e:
                    photo_id = getattr(photo, 'id', '?')
                    html += f'<div style="border: 1px solid red; padding: 5px;">Ошибка фото #{photo_id}</div>'
            html += '</div>'
            return format_html(html)
        except Exception as e:
            obj_id = getattr(obj, 'id', 'None')
            print(f"Error in all_photos_preview for post {obj_id}: {e}")
            return "Ошибка загрузки фотографий"
    all_photos_preview.short_description = "Все фото"
    
    def get_queryset(self, request):
        """Оптимизация запросов"""
        return super().get_queryset(request).select_related(
            'author', 'rubric'
        ).prefetch_related('photos')
    
    actions = ['make_published', 'make_draft', 'make_archived']
    
    def make_published(self, request, queryset):
        """Опубликовать выбранные посты"""
        updated = queryset.update(status='published')
        self.message_user(request, f"{updated} постов опубликовано")
    make_published.short_description = "Опубликовать выбранные посты"
    
    def make_draft(self, request, queryset):
        """Перевести в черновик"""
        updated = queryset.update(status='draft')
        self.message_user(request, f"{updated} постов переведено в черновики")
    make_draft.short_description = "Перевести в черновики"
    
    def make_archived(self, request, queryset):
        """Архивировать"""
        updated = queryset.update(status='archived')
        self.message_user(request, f"{updated} постов архивировано")
    make_archived.short_description = "Архивировать"

class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ['username', 'email', 'first_name', 'last_name', 
                   'patronymic', 'phone_number', 'city', 'posts_count']
    
    fieldsets = UserAdmin.fieldsets + (
        ('Личная информация', {
            'fields': ('patronymic', 'phone_number')
        }),
        ('Адрес', {
            'fields': ('city', 'street', 'house', 'apartment')
        }),
    )
    
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Личная информация', {
            'fields': ('first_name', 'last_name', 'patronymic', 
                      'email', 'phone_number')
        }),
    )
    
    search_fields = ['username', 'email', 'first_name', 'last_name', 
                    'phone_number']
    list_filter = ['city', 'is_staff', 'is_active', 'is_superuser']
    
    def posts_count(self, obj):
        """Количество постов пользователя"""
        return obj.posts.count()
    posts_count.short_description = "Постов"


# Регистрация моделей
admin.site.register(CustomUser, CustomUserAdmin)