from django.contrib import admin
from .models import Rubric
# Register your models here.



@admin.register(Rubric)
class RubricAdmin(admin.ModelAdmin):
    list_display = ('name', 'counter')
    search_fields = ('name',)
    list_filter = ('counter',)
    readonly_fields = ('counter',)