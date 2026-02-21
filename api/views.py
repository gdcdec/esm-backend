from django.shortcuts import render
from rest_framework import viewsets, status, generics, permissions
from rest_framework.decorators import action
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Rubric, CustomUser
from .serializers import RubricSerializer, UserRegistrationSerializer
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from django.contrib.auth import logout
from django.contrib.auth import get_user_model

from .models import PasswordReset
from .serializers import (
    PasswordResetRequestSerializer,
    PasswordResetVerifySerializer,
    PasswordResetConfirmSerializer
)
from datetime import datetime, timedelta#!
from .utils.email_utils import send_password_reset_email

User = get_user_model()
# Create your views here.


class RubricViewSet(viewsets.ModelViewSet):
    """
    ViewSet для работы с рубриками:
    - GET /api/rubrics/ - список всех рубрик
    - POST /api/rubrics/ - создать новую рубрику
    - GET /api/rubrics/{name}/ - получить конкретную рубрику
    - PUT /api/rubrics/{name}/ - обновить рубрику
    - PATCH /api/rubrics/{name}/ - частично обновить
    - DELETE /api/rubrics/{name}/ - удалить рубрику
    """
    queryset = Rubric.objects.all()
    serializer_class = RubricSerializer
    lookup_field = 'name'  # ищем по name вместо id
    
    @action(detail=True, methods=['post'])
    def increment(self, request, name=None):
        """Увеличить счётчик рубрики"""
        rubric = self.get_object()
        rubric.increment_counter()
        return Response({
            'status': 'success',
            'name': rubric.name,
            'counter': rubric.counter
        })
    
    @action(detail=True, methods=['post'])
    def decrement(self, request, name=None):
        """Уменьшить счётчик рубрики"""
        rubric = self.get_object()
        rubric.decrement_counter()
        return Response({
            'status': 'success',
            'name': rubric.name,
            'counter': rubric.counter
        })
    
    @action(detail=False, methods=['get'])
    def top(self, request):
        """Получить топ-5 рубрик по счётчику"""
        top_rubrics = Rubric.objects.order_by('-counter')[:5]
        serializer = self.get_serializer(top_rubrics, many=True)
        return Response(serializer.data)

class UserRegistrationView(generics.CreateAPIView):
    queryset = CustomUser.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Сохраняем пользователя (пароль хешируется в create_user)
        user = serializer.save()
        
        # Создаем токен
        token, created = Token.objects.get_or_create(user=user)
        
        # Формируем ответ
        return Response({
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'patronymic': user.patronymic,
                'phone_number': user.phone_number,
                'city': user.city,
            },
            'token': token.key,
            'message': 'Регистрация успешна'
        }, status=status.HTTP_201_CREATED)

class LogoutView(APIView):
    """
    Выход из системы - удаляет токен пользователя
    """
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            auth_header = request.headers.get('Authorization', '')
            if auth_header.startswith('Token '):
                token_key = auth_header.split(' ')[1]
                
                token = Token.objects.filter(key=token_key).first()
                if token:
                    token.delete()
                    print(f"Token deleted via header")
                    return Response(
                        {"message": "Успешный выход из системы"},
                        status=status.HTTP_200_OK
                    )
            
            
            if hasattr(request.user, 'auth_token'):
                request.user.auth_token.delete()
                return Response(
                    {"message": "Успешный выход из системы"},
                    status=status.HTTP_200_OK
                )
            
            
            tokens = Token.objects.filter(user=request.user)
            if tokens.exists():
                tokens.delete()
                return Response(
                    {"message": "Успешный выход из системы"},
                    status=status.HTTP_200_OK
                )
            
            
            
            return Response(
                {"message": "Пользователь уже вышел из системы"},
                status=status.HTTP_200_OK
            )
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            
            return Response(
                {
                    "error": f"Ошибка при выходе: {str(e)}",
                    "auth_header": request.headers.get('Authorization', 'None'),
                    "user": str(request.user)
                },
                status=status.HTTP_400_BAD_REQUEST
            )

class ChangePasswordView(APIView):
    """Смена пароля"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        user = request.user
        old_password = request.data.get('old_password')
        new_password = request.data.get('new_password')
        
        if not user.check_password(old_password):
            return Response({"error": "Неверный старый пароль"}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        user.set_password(new_password)
        user.save()
        return Response({"message": "Пароль успешно изменен"})

class CustomAuthToken(ObtainAuthToken):# Login
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data,
                                           context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, created = Token.objects.get_or_create(user=user)
        
        return Response({
            'token': token.key,
            'user_id': user.pk,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name
        })
        
        
        
class PasswordResetRequestView(APIView):
    """
    Шаг 1: Запрос на сброс пароля
    Отправляет код подтверждения на email
    """
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        email = serializer.validated_data['email']
        user = serializer.context['user']
        
        # Создаем код сброса
        reset = PasswordReset.create_for_user(user)
        
        # Отправляем код на email
        success, message = send_password_reset_email(email, reset.code)
        
        if success:
            
            #print(f"\nКод сброса для {email}: {reset.code}\n")
            
            return Response({
                'message': 'Код подтверждения отправлен на ваш email',
                'email': email,
                'debug_code': reset.code  # Только для разработки!
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'error': f'Ошибка отправки email: {message}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class PasswordResetVerifyView(APIView):
    """
    Шаг 2: Проверка кода подтверждения
    """
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = PasswordResetVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        return Response({
            'message': 'Код подтвержден',
            'verified': True
        }, status=status.HTTP_200_OK)


class PasswordResetConfirmView(APIView):
    """
    Шаг 3: Установка нового пароля
    """
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = serializer.context['user']
        reset = serializer.context['reset']
        
        # Устанавливаем новый пароль
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        
        # Помечаем код как использованный
        reset.is_used = True
        reset.save()
        
        return Response({
            'message': 'Пароль успешно изменен. Теперь вы можете войти с новым паролем.'
        }, status=status.HTTP_200_OK)


# Дополнительный View для проверки статуса (опционально)
class PasswordResetStatusView(APIView):
    """
    Проверка статуса запроса сброса пароля
    """
    permission_classes = [permissions.AllowAny]
    
    def get(self, request, email):
        try:
            user = User.objects.get(email=email)
            reset = PasswordReset.objects.filter(user=user, is_used=False).first()
            
            if reset and reset.is_valid():
                return Response({
                    'has_active_request': True,
                    'expires_at': reset.expires_at,
                    'time_remaining': str(reset.expires_at - datetime.now())
                })
            else:
                return Response({
                    'has_active_request': False
                })
        except User.DoesNotExist:
            return Response({
                'error': 'Пользователь не найден'
            }, status=status.HTTP_404_NOT_FOUND)