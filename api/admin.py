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
    list_display = ('name', 'counter', 'posts_count')
    search_fields = ('name',)
    list_filter = ('counter',)
    readonly_fields = ('counter', 'posts_count')
    
    def posts_count(self, obj):
        """Количество постов в рубрике"""
        return obj.posts.count()
    posts_count.short_description = "Постов"


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
        """Превью заголовка с обрезанием"""
        if len(obj.title) > 50:
            return f"{obj.title[:50]}..."
        return obj.title
    title_preview.short_description = "Заголовок"
    
    def photo_count_display(self, obj):
        """Отображение количества фото"""
        count = obj.photo_count
        if count:
            return format_html(
                '<b style="color: green;">{} фото</b>',
                count
            )
        return '<span style="color: gray;">нет фото</span>'
    photo_count_display.short_description = "Фото"
    
    def has_photos(self, obj):
        """Есть ли фото"""
        return obj.photos.exists()
    has_photos.boolean = True
    has_photos.short_description = "Есть фото"
    
    def first_photo_preview(self, obj):
        """Превью первого фото"""
        first = obj.first_photo
        if first and first.photo:
            return format_html(
                '<img src="{}" style="max-height: 200px; max-width: 200px;" />',
                first.photo.url
            )
        return "Нет фотографий"
    first_photo_preview.short_description = "Главное фото"
    
    def all_photos_preview(self, obj):
        """Превью всех фото"""
        photos = obj.photos.all()
        if not photos:
            return "Нет фотографий"
        
        html = '<div style="display: flex; flex-wrap: wrap; gap: 10px;">'
        for photo in photos:
            if photo.photo:
                html += format_html(
                    '<div style="border: 1px solid #ddd; padding: 5px;">'
                    '<img src="{}" style="max-height: 100px; max-width: 100px;" /><br/>'
                    '<small>{}: {}</small>'
                    '</div>',
                    photo.photo.url,
                    photo.order,
                    photo.caption or 'без подписи'
                )
        html += '</div>'
        return format_html(html)
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


@admin.register(PostPhoto)
class PostPhotoAdmin(admin.ModelAdmin):
    """
    Админка для фотографий
    """
    list_display = ['id', 'post_link', 'order', 'caption', 'uploaded_at', 'photo_preview']
    list_filter = ['uploaded_at', 'post__rubric']
    search_fields = ['caption', 'post__title']
    readonly_fields = ['uploaded_at', 'photo_preview']
    
    def post_link(self, obj):
        """Ссылка на пост"""
        return format_html(
            '<a href="/admin/api/post/{}/change/">Пост #{}</a>',
            obj.post.id, obj.post.id
        )
    post_link.short_description = "Пост"
    
    def photo_preview(self, obj):
        """Превью фото"""
        if obj.photo:
            return format_html(
                '<img src="{}" style="max-height: 100px; max-width: 100px;" />',
                obj.photo.url
            )
        return "Нет фото"
    photo_preview.short_description = "Превью"
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('post')


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