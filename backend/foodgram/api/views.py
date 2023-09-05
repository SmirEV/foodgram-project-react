from api.filters import IngredientFilter, RecipeFilter, UserFilter
from api.pagination import CustomPagination
from api.serializers import (AuthorSerializer, AuthorWithRecipesSerializer,
                             FavoritesSerializer, IngredientSerializer,
                             RecipeCreateSerializer, RecipeSerializer,
                             RecipeShortSerializer,
                             ShoppingCartSerializer, SubscribeSerializer,
                             TagSerializer, UserCreateSerializer)
from api.utils import generate_pdf
# from django.db import IntegrityError
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from recipes.models import (Favorites, Ingredient, MyShoppingCart, Recipe,
                            RecipeIngredient, Subscribtions, Tag, User)
from rest_framework import filters, status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet


class CustomUserViewSet(UserViewSet):
    """
    Вьюсет для эндпоинтов /users/,
    /users/subscribe, /users/set_password/.
    """
    queryset = User.objects.all()
    serializer_class = AuthorSerializer
    pagination_class = CustomPagination
    # filterset_class = UserFilter
    filter_backends = (DjangoFilterBackend, filters.SearchFilter,)
    search_fields = ('username', 'email')
    permission_classes = (AllowAny, )

    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        return AuthorSerializer

    @action(detail=True, methods=['post', 'delete'])
    def subscribe(self, request, id=None):
        user = self.request.user
        author = User.objects.get(id=id)
        if request.method == 'POST':
            if user == author:
                return Response(
                    {'error': ' Ошибка подписки'},
                    status=status.HTTP_400_BAD_REQUEST)
            serializer = SubscribeSerializer(
                Subscribtions.objects.create(
                    user=request.user,
                    author=author),
                context={'request': request})
            return Response(serializer.data,
                            status=status.HTTP_201_CREATED)
        if request.method == 'DELETE':
            subscription = Subscribtions.objects.filter(
                user=request.user, author=author).first()
            if subscription:
                subscription.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            else:
                return Response(
                    {'errors': 'Вы не подписаны на этого автора.'},
                    status=status.HTTP_400_BAD_REQUEST)

    @action(methods=['GET'],
            detail=False,
            permission_classes=(IsAuthenticated, )
            )
    def subscriptions(self, request):
        """ Получить на кого пользователь подписан. """
        serializer = SubscribeSerializer(
            Subscribtions.objects.filter(user=request.user),
            many=True,
            context={'request': request})
        return serializer.data

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
    # queryset = Recipe.objects.all().order_by('-id')
    serializer_class = RecipeSerializer
    pagination_class = CustomPagination
    filterset_class = RecipeFilter
    filter_backends = (DjangoFilterBackend, )

    def get_queryset(self):
        recipes = Recipe.objects.prefetch_related(
            'recipe_ingredients__ingredient',
            'tags').all().order_by('-id')
        return recipes

    def get_serializer_class(self):
        if self.action == 'get':
            if 'is_in_shopping_cart' in self.request.GET:
                return RecipeShortSerializer
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
            'user': request.user,
            'recipe': recipe
        }
        serializer = FavoritesSerializer(data=data, context=context)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @favorite.mapping.delete
    def destroy_favorite(self, request, pk):
        recipe = get_object_or_404(Recipe, id=pk)
        get_object_or_404(
            Favorites,
            user=request.user,
            recipe=recipe).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=('POST',))
    def shopping_cart(self, request, pk):
        context = {'request': request}
        recipe = get_object_or_404(Recipe, id=pk)
        data = {
            'user': request.user,
            'recipe': recipe
        }
        serializer = ShoppingCartSerializer(data=data, context=context)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @shopping_cart.mapping.delete
    def destroy_shopping_cart(self, request, pk):
        recipe = get_object_or_404(Recipe, id=pk)
        get_object_or_404(
            MyShoppingCart,
            user=request.user,
            recipe=recipe).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
