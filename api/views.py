from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Rubric
from .serializers import RubricSerializer
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