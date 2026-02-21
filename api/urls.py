# api/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from .views import (
    CustomAuthToken, 
    UserRegistrationView, 
    LogoutView,
    ChangePasswordView,
    PasswordResetRequestView,
    PasswordResetVerifyView,
    PasswordResetConfirmView,
    # Добавляем новые импорты для постов
    PostListView,
    PostDetailView,
    PostPhotoUploadView,
    PostPhotoDeleteView
)

# router используем когда с таблицей однотипные действия делают
router = DefaultRouter()
router.register(r'rubrics', views.RubricViewSet, basename='rubric')


urlpatterns = [
    # Все API с префиксом /api/
    
        # Маршруты от роутера (будут /api/rubrics/, /api/rubrics/1/)
        path('', include(router.urls)),
        
        # Посты
        path('posts/', views.PostListView.as_view(), name='post-list'),
        path('posts/<int:pk>/', views.PostDetailView.as_view(), name='post-detail'),
        path('users/<int:user_id>/posts/', views.UserPostListView.as_view(), name='user-posts'),
        
        # Фотографии постов
        path('posts/photos/upload/', views.PostPhotoUploadView.as_view(), name='post-photo-upload'),
        path('posts/photos/<int:pk>/', views.PostPhotoDeleteView.as_view(), name='post-photo-delete'),
        
        
        # Аутентификация
        path('auth/', include([
            path('register/', UserRegistrationView.as_view(), name='user-register'),
            path('login/', CustomAuthToken.as_view(), name='user-login'),
            path('logout/', views.LogoutView.as_view(), name='user-logout'),
            # path('password-reset/', views.PasswordResetView.as_view()),
            path('password-reset/request/', views.PasswordResetRequestView.as_view(), name='password-reset-request'),
            path('password-reset/verify/', views.PasswordResetVerifyView.as_view(), name='password-reset-verify'),
            path('password-reset/confirm/', views.PasswordResetConfirmView.as_view(), name='password-reset-confirm'),
            path('password-reset/status/<str:email>/', views.PasswordResetStatusView.as_view(), name='password-reset-status'),
            
            
        ])),
        
    
]




# Сброс пароля
