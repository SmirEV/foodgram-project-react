from django.shortcuts import render, HttpResponse
from djoser.views import UserViewSet

from rest_framework.viewsets import ModelViewSet
from recipes.models import Tag, Recipe
from api.serializers import TagSerializer, RecipeSerializer


def index(request):
    return HttpResponse('index')


class CustomUserViewSet(UserViewSet):
    pass


class TagViewSet(ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class RecipeViewSet(ModelViewSet):
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
