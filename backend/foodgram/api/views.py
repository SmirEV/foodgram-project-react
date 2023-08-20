from django.db import IntegrityError
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from api.filters import IngredientFilter, RecipeFilter, UserFilter
from api.pagination import CustomPagination
from api.serializers import (AuthorSerializer, AuthorWithRecipesSerializer,
                             FavoritesSerializer, IngredientSerializer,
                             RecipeCreateSerializer, RecipeSerializer,
                             ShoppingCartSerializer, TagSerializer,
                             UserCreateSerializer)
from api.utils import generate_pdf
from recipes.models import (Favorites, Ingredient, IsSubscribed,
                            MyShoppingCart, Recipe, RecipeIngredient, Tag,
                            User)


class CustomUserViewSet(UserViewSet):
    """
    Вьюсет для эндпоинтов /users/,
    /users/subscribe, /users/set_password/.
    """
    serializer_class = AuthorSerializer
    pagination_class = CustomPagination
    filterset_class = UserFilter
    filter_backends = (DjangoFilterBackend, )
    permission_classes = (AllowAny, )

    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        return AuthorSerializer

    @action(detail=True, methods=['post', 'delete'])
    def subscribe(self, request, id=None):
        '''
        Поняла замечание про валидацию. В моем представлении
        для того, чтобы сделать валидацию для IsSubscribed на уровне
        сериализатора, нужно написать для этой модели отдельный сериализатор
        + отдельную вьюху. Перепишу, если не проверите до ночи)
        '''
        user = self.request.user
        author = User.objects.get(id=id)
        if request.method == 'POST':
            if user == author:
                return Response(
                    {'error': ' Ошибка подписки'},
                    status=status.HTTP_400_BAD_REQUEST)
            try:
                IsSubscribed(
                    user=user,
                    author=author).save()
            except IntegrityError:
                return Response(
                    {'error': 'Ошибка подписки'},
                    status=status.HTTP_400_BAD_REQUEST)
            serializer = AuthorSerializer(
                instance=author,
                context={'request': request})
            return Response(serializer.data)
        if request.method == 'DELETE':
            id = IsSubscribed.objects.get(user=user, author=author).id
            IsSubscribed(id=id).delete()
            return Response()

    @action(detail=False,
            methods=['post'])
    def set_password(self, request):
        print(request.data)
        user = request.user
        current_password = request.data.get('current_password')
        new_password = request.data.get('new_password')

        if not user.check_password(current_password):
            return Response({'error': 'Invalid old password'},
                            status=status.HTTP_400_BAD_REQUEST)

        user.set_password(new_password)
        user.save()

        return Response({'message': 'Password successfully changed'},
                        status=status.HTTP_200_OK)


class AuthorViewSet(UserViewSet):
    """ Вьюсет для авторов с рецептами. """
    serializer_class = AuthorWithRecipesSerializer
    pagination_class = CustomPagination
    filterset_class = UserFilter
    filter_backends = (DjangoFilterBackend, )

    def get_queryset(self):
        user = self.request.user
        queryset = User.objects.filter(following__user=user)
        return queryset


class TagViewSet(ModelViewSet):
    """ Вьюсет для тегов. """
    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class IngredientViewSet(ModelViewSet):
    """ Вьюсет для ингредиентов. """
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filterset_class = IngredientFilter
    filter_backends = (DjangoFilterBackend, )


class RecipeViewSet(ModelViewSet):
    """ Вьюсет для рецептов. """
    queryset = Recipe.objects.all().order_by('-id')
    serializer_class = RecipeSerializer
    pagination_class = CustomPagination
    filterset_class = RecipeFilter
    filter_backends = (DjangoFilterBackend, )

    def get_queryset(self):
        recipes = Recipe.objects.prefetch_related(
            'recipe_ingredients__ingredient',
            'tags').all().order_by('-id')
        return recipes

    #def get_serializer_class(self):
    #    if self.action in ('create', 'update'):
    #        return RecipeCreateSerializer
    #    return RecipeSerializer

    def get_serializer_class(self):
        if self.action == 'get':
            return RecipeSerializer
        return RecipeCreateSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def perform_update(self, serializer):
        serializer.save(author=self.request.user)

    @action(detail=False, methods=['get'])
    def download_shopping_cart(self, request):
        user = User.objects.prefetch_related('cooker__recipe').get(
            id=request.user.id)
        recipe_ids = user.cooker.all().values_list('recipe', flat=True)
        shopping_cart = dict()
        for ind in recipe_ids:
            recipe = Recipe.objects.get(id=ind)
            ingredients = recipe.ingredients.all()
            for i in ingredients:
                amount = RecipeIngredient.objects.get(
                    ingredient=i, recipe=recipe).amount
                if i.name not in shopping_cart.keys():
                    shopping_cart.update(
                        {i.name: [amount, i.measurement_unit]})
                else:
                    shopping_cart.update({i.name: [
                        amount + shopping_cart[i.name][0],
                        i.measurement_unit]})
        return generate_pdf(request, shopping_cart)

    @action(detail=True, methods=('post',))
    def favorite(self, request, pk):
        context = {"request": request}
        recipe = get_object_or_404(Recipe, id=pk)
        data = {
            'user': request.user.id,
            'recipe': recipe.id
        }
        serializer = FavoritesSerializer(data=data, context=context)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @favorite.mapping.delete
    def destroy_favorite(self, request, pk):
        get_object_or_404(
            Favorites,
            user=request.user,
            recipe=get_object_or_404(Recipe, id=pk)).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=('POST',))
    def shopping_cart(self, request, pk):
        context = {'request': request}
        recipe = get_object_or_404(Recipe, id=pk)
        data = {
            'user': request.user.id,
            'recipe': recipe.id
        }
        serializer = ShoppingCartSerializer(data=data, context=context)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @shopping_cart.mapping.delete
    def destroy_shopping_cart(self, request, pk):
        get_object_or_404(
            MyShoppingCart,
            user=request.user.id,
            recipe=get_object_or_404(Recipe, id=pk)
        ).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
