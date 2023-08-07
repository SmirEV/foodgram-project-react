from rest_framework import routers
from django.urls import path, include

from api.views import (index, CustomUserViewSet,
                       TagViewSet, RecipeViewSet,
                       IngredientViewSet, FavoriteViewSet,
                       ShoppingCartViewSet)


router = routers.DefaultRouter()
router.register('users', CustomUserViewSet)
router.register(r'users/(?P<pk>\d+)/subscribe',
                CustomUserViewSet,
                basename='user-subscribe')
router.register(r'users/subscriptions',
                CustomUserViewSet,
                basename='subscriptions')
router.register('tags', TagViewSet)
router.register(r'recipes/(?P<id>\d+)/favorite',
                FavoriteViewSet,
                basename='recipe-favorite')
router.register(r'recipes/(?P<id>\d+)/shopping_cart',
                ShoppingCartViewSet,
                basename='recipe-shopping-cart')
router.register('recipes', RecipeViewSet)
router.register(r'users/download_shopping_cart',
                RecipeViewSet,
                basename='download_shopping_cart')
router.register('ingredients', IngredientViewSet)

urlpatterns = [
    path('index', index),
    path('auth/', include('djoser.urls.authtoken')),
    path('', include(router.urls)),
]
