from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.admin.models import LogEntry, ADDITION, CHANGE, DELETION
from django.contrib.contenttypes.models import ContentType
from django.utils.html import format_html
from django.utils import timezone
from django.urls import reverse
from django.db import models
from django.db.models import Count, Q
from .models import Rubric, CustomUser, Post, PostPhoto, Notification  # Уберите NotificationType из импорта
from django.conf import settings
from .utils.notifications import (
    notify_user_about_post_status_change,
    notify_user_about_post_edit,
    notify_user_about_post_deletion,
    notify_user_about_user_data_change,
    send_admin_notification,
)


class PostPhotoInline(admin.TabularInline):
    """Инлайн для отображения фотографий внутри поста"""
    model = PostPhoto
    extra = 1
    fields = ['photo', 'caption', 'order', 'photo_preview']
    readonly_fields = ['photo_preview']
    
    def photo_preview(self, obj):
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
    Админка для постов с уведомлениями
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
    
    inlines = [PostPhotoInline]
    
    def save_model(self, request, obj, form, change):
        """
        Сохранение поста с уведомлением об изменениях
        """
        old_obj = None
        changed_fields = []
        
        if change:
            # Получаем старую версию объекта
            old_obj = self.model.objects.get(pk=obj.pk)
            
            # Определяем какие поля изменились
            for field in form.changed_data:
                if field in ['title', 'description', 'address', 'rubric', 
                            'latitude', 'longitude']:
                    changed_fields.append(field)
        
        # Сохраняем объект
        super().save_model(request, obj, form, change)
        
        # Отправляем уведомления
        if change and old_obj and obj.author != request.user:
            # Если изменился статус
            if 'status' in form.changed_data:
                notify_user_about_post_status_change(
                    obj, old_obj.status, obj.status, request.user
                )
            
            # Если изменились другие поля
            if changed_fields:
                notify_user_about_post_edit(obj, request.user, changed_fields)
        
        # Если это новый пост и он сразу опубликован
        elif not change and obj.status == 'published' and obj.author != request.user:
            send_admin_notification(
                user=obj.author,
                subject=f"Ваш пост \"{obj.title}\" опубликован",
                message=f"Администратор {request.user.get_full_name() or request.user.username} "
                       f"опубликовал ваш пост \"{obj.title}\".",
                notification_type='success',
                link=f'/posts/{obj.id}/',
                admin_user=request.user,
                action_type='create_published',
                object_repr=obj.title
            )
    
    def delete_model(self, request, obj):
        """
        Удаление поста с уведомлением
        """
        # Отправляем уведомление автору, если автор не администратор
        if obj.author != request.user:
            notify_user_about_post_deletion(obj, request.user)
        
        super().delete_model(request, obj)
    
    def get_queryset(self, request):
        """Оптимизация запросов"""
        return super().get_queryset(request).select_related(
            'author', 'rubric'
        ).prefetch_related('photos')
    
    actions = ['make_published', 'make_draft', 'make_archived']
    
    def make_published(self, request, queryset):
        """Опубликовать выбранные посты с уведомлением"""
        count = 0
        for post in queryset:
            old_status = post.status
            if old_status != 'published':
                post.status = 'published'
                post.save()
                count += 1
                
                # Уведомляем автора
                if post.author != request.user:
                    notify_user_about_post_status_change(
                        post, old_status, 'published', request.user
                    )
        
        self.message_user(request, f"{count} постов опубликовано")
    make_published.short_description = "Опубликовать выбранные посты"
    
    def make_draft(self, request, queryset):
        """Перевести в черновик с уведомлением"""
        count = 0
        for post in queryset:
            old_status = post.status
            if old_status != 'draft':
                post.status = 'draft'
                post.save()
                count += 1
                
                if post.author != request.user:
                    notify_user_about_post_status_change(
                        post, old_status, 'draft', request.user
                    )
        
        self.message_user(request, f"{count} постов переведено в черновики")
    make_draft.short_description = "Перевести в черновики"
    
    def make_archived(self, request, queryset):
        """Архивировать с уведомлением"""
        count = 0
        for post in queryset:
            old_status = post.status
            if old_status != 'archived':
                post.status = 'archived'
                post.save()
                count += 1
                
                if post.author != request.user:
                    notify_user_about_post_status_change(
                        post, old_status, 'archived', request.user
                    )
        
        self.message_user(request, f"{count} постов архивировано")
    make_archived.short_description = "Архивировать"
    
    # Вспомогательные методы для отображения
    def title_preview(self, obj):
        if not obj:
            return "[Нет объекта]"
        if obj.title is None:
            return "[Без заголовка]"
        title_str = str(obj.title) if not isinstance(obj.title, str) else obj.title
        if title_str == "":
            return "[Пустой заголовок]"
        if len(title_str) > 50:
            return f"{title_str[:50]}..."
        return title_str
    title_preview.short_description = "Заголовок"
    
    def photo_count_display(self, obj):
        try:
            count = obj.photo_count
            if count:
                return format_html('<b style="color: green;">{} фото</b>', count)
        except:
            pass
        return '<span style="color: gray;">нет фото</span>'
    photo_count_display.short_description = "Фото"
    
    def has_photos(self, obj):
        try:
            return obj.photos.exists()
        except:
            return False
    has_photos.boolean = True
    has_photos.short_description = "Есть фото"
    
    def first_photo_preview(self, obj):
        try:
            if not obj:
                return "Нет объекта"
            first = obj.first_photo
            if first and first.photo:
                return format_html(
                    '<img src="{}" style="max-height: 200px; max-width: 200px;" />',
                    first.photo.url
                )
        except Exception as e:
            print(f"Error: {e}")
        return "Нет фотографий"
    first_photo_preview.short_description = "Главное фото"
    
    def all_photos_preview(self, obj):
        try:
            if not obj:
                return "Нет объекта"
            photos = obj.photos.all()
            if not photos:
                return "Нет фотографий"
            html = '<div style="display: flex; flex-wrap: wrap; gap: 10px;">'
            for photo in photos:
                try:
                    if photo and photo.photo:
                        order = photo.order if photo.order is not None else '?'
                        caption = photo.caption or 'без подписи'
                        html += format_html(
                            '<div style="border: 1px solid #ddd; padding: 5px;">'
                            '<img src="{}" style="max-height: 100px; max-width: 100px;" /><br/>'
                            '<small>{}: {}</small>'
                            '</div>',
                            photo.photo.url, order, caption
                        )
                except Exception:
                    continue
            html += '</div>'
            return format_html(html)
        except Exception:
            return "Ошибка загрузки"
    all_photos_preview.short_description = "Все фото"


class CustomUserAdmin(UserAdmin):
    """Админка для пользователей с уведомлениями"""
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
    
    def save_model(self, request, obj, form, change):
        """
        Сохранение пользователя с уведомлением об изменениях
        """
        changed_fields = []
        
        if change:
            # Получаем старую версию объекта
            old_obj = self.model.objects.get(pk=obj.pk)
            
            # Определяем какие поля изменились
            for field in form.changed_data:
                if field in ['first_name', 'last_name', 'patronymic', 'email',
                            'phone_number', 'city', 'street', 'house', 'apartment']:
                    changed_fields.append(field)
        
        # Сохраняем объект
        super().save_model(request, obj, form, change)
        
        # Отправляем уведомление, если данные изменились и пользователь не администратор
        if change and changed_fields and obj != request.user:
            notify_user_about_user_data_change(obj, request.user, changed_fields)
    
    def posts_count(self, obj):
        """Количество постов пользователя"""
        return obj.posts.count()
    posts_count.short_description = "Постов"


# Регистрация админки для уведомлений
@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    """
    Админка для уведомлений (упрощенная версия)
    """
    list_display = ['id', 'user', 'subject', 'notification_type', 'is_read', 'created_at']
    list_filter = ['notification_type', 'is_read', 'created_at']
    search_fields = ['subject', 'message', 'user__username', 'user__email']
    readonly_fields = ['id', 'created_at', 'read_at']
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('user', 'subject', 'message', 'notification_type')
        }),
        ('Статус', {
            'fields': ('is_read', 'read_at'),
        }),
        ('Дополнительно', {
            'fields': ('link', 'metadata'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['mark_as_read', 'mark_as_unread']
    
    def mark_as_read(self, request, queryset):
        count = queryset.filter(is_read=False).update(is_read=True, read_at=timezone.now())
        self.message_user(request, f'{count} уведомлений отмечено как прочитанные')
    mark_as_read.short_description = "Отметить как прочитанные"
    
    def mark_as_unread(self, request, queryset):
        count = queryset.filter(is_read=True).update(is_read=False, read_at=None)
        self.message_user(request, f'{count} уведомлений отмечено как непрочитанные')
    mark_as_unread.short_description = "Отметить как непрочитанные"


# Регистрация моделей
admin.site.register(CustomUser, CustomUserAdmin)