from django.urls import include, path
from rest_framework import routers

from api.views import (AuthorViewSet, CustomUserViewSet, IngredientViewSet,
                       RecipeViewSet, TagViewSet)

router = routers.DefaultRouter()
router.register(r'users/subscriptions',
                AuthorViewSet,
                basename='subscriptions')
router.register('users', CustomUserViewSet)
router.register(r'users/(?P<pk>\d+)/subscribe',
                CustomUserViewSet,
                basename='user-subscribe')
router.register('tags', TagViewSet)

router.register('recipes', RecipeViewSet)
router.register(r'users/download_shopping_cart',
                RecipeViewSet,
                basename='download_shopping_cart')
router.register('ingredients', IngredientViewSet)

urlpatterns = [
    path('auth/', include('djoser.urls.authtoken')),
    path('', include(router.urls)),
]
