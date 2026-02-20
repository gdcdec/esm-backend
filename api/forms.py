# api/forms.py (создайте новый файл)
from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    phone_number = forms.CharField(required=False)
    city = forms.CharField(required=False)
    
    class Meta:
        model = CustomUser
        fields = [
            'username', 'email', 'password1', 'password2',
            'first_name', 'last_name', 'patronymic',
            'phone_number', 'city', 'street', 'house', 'apartment'
        ]
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user