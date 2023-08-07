import io
from django.shortcuts import render, HttpResponse
from djoser.views import UserViewSet
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework import status
from django.db import IntegrityError
from django.http import HttpResponse, FileResponse

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from rest_framework.viewsets import ModelViewSet
from recipes.models import (User,Tag, Recipe, Ingredient,
                            IsSubscribed, Favorites,
                            MyShoppingCart, RecipeIngredient)
from api.serializers import (IngredientSerializer, TagSerializer,
                             RecipeSerializer, RecipeCreateSerializer,
                             AuthorSerializer, UserCreateSerializer,
                             AuthorWithRecipesSerializer,
                             RecipeShortSerializer)
from api.pagination import CustomPagination


def index(request):
    return HttpResponse('index')


def generate_pdf(request, data):
    # Create a file-like buffer to receive PDF data.
    buffer = io.BytesIO()

    # Create the PDF object, using the buffer as its "file."
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

    @action(detail=False, methods=['get'])
    def subscriptions(self, request):
        user = self.request.user
        authors = User.objects.filter(following__user=user)
        serializer = AuthorWithRecipesSerializer(
                instance=authors,
                context={'request': request},
                many=True)
        return Response(serializer.data)


class TagViewSet(ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class IngredientViewSet(ModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer


class RecipeViewSet(ModelViewSet):
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    pagination_class = CustomPagination

    def get_queryset(self):
        recipes = Recipe.objects.prefetch_related(
            'recipe_ingredients__ingredient',
            'tags').all()
        return recipes

    def get_serializer_class(self):
        if self.action == 'create':
            return RecipeCreateSerializer
        return RecipeSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(detail=False, methods=['get'])
    def download_shopping_cart(self, request):
        user = User.objects.prefetch_related('cooker__recipe').get(id=request.user.id)
        recipe_ids = user.cooker.all().values_list('recipe', flat=True)
        shopping_cart = dict()
        for ind in recipe_ids:
            recipe = Recipe.objects.get(id=ind)
            ingredients = recipe.ingredients.all()
            for i in ingredients:
                amount = RecipeIngredient.objects.get(
                    ingredient=i, recipe=recipe).amount
                if i.name not in shopping_cart.keys():
                    shopping_cart.update({i.name: [amount, i.measurement_unit]})
                elif i.measurement_unit == shopping_cart[i.name][-1]:
                    shopping_cart.update({i.name: [amount, i.measurement_unit + shopping_cart[i.name][0]]})
                else:
                    return Response(
                        {'error':
                         'Ошибка добавления в список покупок: ' +
                         'невозможно сложить величины ' +
                         f'{shopping_cart[i.name][-1]} и {i.measurement_unit}'})
        return generate_pdf(request, shopping_cart)


class FavoriteViewSet(ModelViewSet):
    queryset = Recipe.objects.all()

    def create(self, request, id=None):
        recipe = self.get_object()
        try:
            Favorites(
                user=request.user,
                recipe=recipe).save()
        except IntegrityError:
            return Response(
                {'error': 'Ошибка добавления в избранное'},
                status=status.HTTP_400_BAD_REQUEST)
        serializer = RecipeShortSerializer(recipe)
        return Response(serializer.data)

    def destroy(self, request, id=None):
        recipe = self.get_object()
        id = Favorites.objects.get(
            user=request.user,
            recipe=recipe).id
        Favorites(id=id).delete()
        return Response()

    def delete(self, request, id):
        return self.destroy(request, id)

    def get_object(self):
        return self.queryset.get(id=self.kwargs['id'])


class ShoppingCartViewSet(ModelViewSet):
    queryset = Recipe.objects.all()

    def create(self, request, id=None):
        recipe = self.get_object()
        try:
            MyShoppingCart(
                user=request.user,
                recipe=recipe).save()
        except IntegrityError:
            return Response(
                {'error': 'Ошибка добавления в корзину'},
                status=status.HTTP_400_BAD_REQUEST)
        serializer = RecipeShortSerializer(recipe)
        return Response(serializer.data)

    def destroy(self, request, id=None):
        recipe = self.get_object()
        id = MyShoppingCart.objects.get(
            user=request.user,
            recipe=recipe).id
        MyShoppingCart(id=id).delete()
        return Response()

    def delete(self, request, id):
        return self.destroy(request, id)

    def get_object(self):
        return self.queryset.get(id=self.kwargs['id'])
