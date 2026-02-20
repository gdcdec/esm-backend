from django.shortcuts import render
from rest_framework import viewsets, status, generics, permissions
from rest_framework.decorators import action
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Rubric, CustomUser
from .serializers import RubricSerializer, CustomUserSerializer
from .serializers import CustomUserSerializer
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.permissions import IsAuthenticated
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
    serializer_class = CustomUserSerializer
    permission_classes = [permissions.AllowAny]
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Сохраняем пользователя
        user = serializer.save()
        
        # Токен создается автоматически сигналом
        token = Token.objects.get(user=user)
        
        headers = self.get_success_headers(serializer.data)
        return Response({
            'user': serializer.data,
            'token': token.key
        }, status=status.HTTP_201_CREATED, headers=headers)

class LogoutView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        # Удаляем токен пользователя
        request.user.auth_token.delete()
        return Response(
            {"message": "Успешный выход из системы"},
            status=status.HTTP_200_OK
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
            'email': user.email,
            'username': user.username
        })