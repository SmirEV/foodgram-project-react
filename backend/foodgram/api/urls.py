from rest_framework import routers
from django.urls import path, include

from api.views import (index, CustomUserViewSet,
                       TagViewSet, RecipeViewSet,
                       IngredientViewSet)


router = routers.DefaultRouter()
router.register('users', CustomUserViewSet)
router.register(r'users/(?P<pk>\d+)/subscribe',
                CustomUserViewSet,
                basename='user-subscribe')
router.register(r'users/subscriptions',
                CustomUserViewSet,
                basename='subscriptions')
router.register('tags', TagViewSet)
router.register('recipes', RecipeViewSet)
router.register('ingredients', IngredientViewSet)

urlpatterns = [
    path('index', index),
    path('auth/', include('djoser.urls.authtoken')),
    path('', include(router.urls)),
]
