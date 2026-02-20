from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Rubric
from .models import CustomUser
# Register your models here.



@admin.register(Rubric)
class RubricAdmin(admin.ModelAdmin):
    list_display = ('name', 'counter')
    search_fields = ('name',)
    list_filter = ('counter',)
    readonly_fields = ('counter',)

#@admin.register(UserAdmin)
class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ['username', 'email', 'first_name', 'last_name', 
                   'patronymic', 'phone_number', 'city']
    
    # Поля для отображения в форме редактирования
    fieldsets = UserAdmin.fieldsets + (
        ('Личная информация', {
            'fields': ('patronymic', 'phone_number')
        }),
        ('Адрес', {
            'fields': ('city', 'street', 'house', 'apartment')
        }),
    )
    
    # Поля для формы создания
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Личная информация', {
            'fields': ('first_name', 'last_name', 'patronymic', 
                      'email', 'phone_number')
        }),
    )
    
    # Поля для поиска
    search_fields = ['username', 'email', 'first_name', 'last_name', 
                    'phone_number']
    
    # Поля для фильтрации
    list_filter = ['city', 'is_staff', 'is_active', 'is_superuser']

admin.site.register(CustomUser, CustomUserAdmin)