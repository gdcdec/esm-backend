# api/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from .views import CustomAuthToken, UserRegistrationView

# router используем когда с таблицей однотипные действия делают
router = DefaultRouter()
router.register(r'rubrics', views.RubricViewSet, basename='rubric')


urlpatterns = [
    # Все API с префиксом /api/
    
        # Маршруты от роутера (будут /api/rubrics/, /api/rubrics/1/)
        path('', include(router.urls)),
        
        # Аутентификация
        path('auth/', include([
            path('register/', UserRegistrationView.as_view(), name='user-register'),
            path('login/', CustomAuthToken.as_view(), name='user-login'),
            path('logout/', views.LogoutView.as_view(), name='user-logout'),
            # path('password-reset/', views.PasswordResetView.as_view()),
        ])),
    
]
