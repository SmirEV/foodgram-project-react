import io

from api.pagination import CustomPagination
from api.serializers import (AuthorSerializer, AuthorWithRecipesSerializer,
                             FavoritesSerializer, IngredientSerializer,
                             RecipeCreateSerializer, RecipeSerializer,
                             ShoppingCartSerializer, TagSerializer,
                             UserCreateSerializer)
from django.db import IntegrityError
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import (DjangoFilterBackend, FilterSet,
                                           filters)
from djoser.views import UserViewSet
from recipes.models import (Favorites, Ingredient, IsSubscribed,
                            MyShoppingCart, Recipe, RecipeIngredient, Tag,
                            User)
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet


class IngredientFilter(SearchFilter):
    search_param = 'name'

    class Meta:
        model = Ingredient
        fields = ('name',)


class RecipeFilter(FilterSet):
    tags = filters.ModelMultipleChoiceFilter(
        field_name='tags__slug',
        to_field_name='slug',
        queryset=Tag.objects.all(),
    )
    is_favorited = filters.NumberFilter(method='filter_is_favorited')
    is_in_shopping_cart = filters.NumberFilter(
        method='filter_is_in_shopping_cart'
    )

    class Meta:
        model = Recipe
        fields = ('tags', 'author', 'is_favorited', 'is_in_shopping_cart',)

    def filter_is_favorited(self, queryset, name, value):
        if value and self.request.user.is_authenticated:
            return queryset.filter(favorite_recipe__user=self.request.user)
        return queryset

    def filter_is_in_shopping_cart(self, queryset, name, value):
        if value and self.request.user.is_authenticated:
            return queryset.filter(for_cooking__user=self.request.user)
        return queryset


class UserFilter(FilterSet):
    username = filters.CharFilter(lookup_expr='icontains')
    email = filters.CharFilter(lookup_expr='icontains')

    class Meta:
        model = User
        fields = ('username', 'email',)

    def filter_username(self, queryset, name, value):
        if value:
            return queryset.filter(username__icontains=value)
        return queryset

    def filter_email(self, queryset, name, value):
        if value:
            return queryset.filter(email__icontains=value)
        return queryset


def generate_pdf(request, data):
    buffer = io.BytesIO()

    pdf_canvas = canvas.Canvas(buffer, pagesize=A4)
    pdfmetrics.registerFont(TTFont('DejaVuSans', 'DejaVuSans.ttf'))
    pdf_canvas.setFont("DejaVuSans", 18)
    y = 750
    pdf_canvas.drawString(50, y, 'СПИСОК ПОКУПОК:')
    y -= 20
    for key, value in data.items():
        y -= 20
        text = u'- {item}:  {amount} {unit}'.format(
            item=key, amount=value[0], unit=value[1])
        text = text.encode('utf-8')
        pdf_canvas.drawString(50, y, text)

    pdf_canvas.showPage()
    pdf_canvas.save()

    buffer.seek(0)
    return FileResponse(buffer, as_attachment=True, filename="data.pdf")


class CustomUserViewSet(UserViewSet):
    serializer_class = AuthorSerializer
    pagination_class = CustomPagination
    filterset_class = UserFilter
    filter_backends = (DjangoFilterBackend, )

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
    serializer_class = AuthorWithRecipesSerializer
    pagination_class = CustomPagination
    filterset_class = UserFilter
    filter_backends = (DjangoFilterBackend, )

    def get_queryset(self):
        user = self.request.user
        queryset = User.objects.filter(following__user=user)
        return queryset


class TagViewSet(ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class IngredientViewSet(ModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer


class RecipeViewSet(ModelViewSet):
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

    def get_serializer_class(self):
        if self.action == 'get':
            return RecipeSerializer
        return RecipeCreateSerializer

    def perform_create(self, serializer):
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

    @action(
        detail=True,
        methods=('post',))
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

    @action(
        detail=True,
        methods=('POST',))
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
