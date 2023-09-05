import django_filters
from django.db.models import Q
from django_filters.rest_framework import FilterSet, filters
from recipes.models import Ingredient, Recipe, Tag, User


class IngredientsNameFilter(django_filters.Filter):
    """ Фильтр для поиска по первым символам названия. """
    def filter(self, qs, value):
        if value:
            return qs.filter(Q(name__istartswith=value))
        return qs


class IngredientFilter(FilterSet):
    """ Фильтр для ингредиентов. """
    name = IngredientsNameFilter()

    class Meta:
        model = Ingredient
        fields = ('name',)


class RecipeFilter(FilterSet):
    """ Фильтр для рецептов. """
    tags = filters.ModelMultipleChoiceFilter(
        field_name='tags__slug',
        to_field_name='slug',
        queryset=Tag.objects.all(),
    )
    is_favorited = filters.BooleanFilter(method='filter_is_favorited')
    is_in_shopping_cart = filters.BooleanFilter(
        field_name='is_in_shopping_cart',
        method='filter_is_in_shopping_cart')

    class Meta:
        model = Recipe
        fields = ('tags', 'author', 'is_favorited', 'is_in_shopping_cart')

    def filter_is_favorited(self, queryset, name, value):
        if value and self.request.user.is_authenticated:
            return queryset.filter(favorite_recipe__user=self.request.user)
        return queryset

    def filter_is_in_shopping_cart(self, queryset, name, value):
        if value and self.request.user.is_authenticated:
            return queryset.filter(in_shopping_cart__cooker=self.request.user)
        return queryset


class UserFilter(FilterSet):
    """ Фильтр для пользователей. """
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
