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

class CustomAuthToken(ObtainAuthToken):
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