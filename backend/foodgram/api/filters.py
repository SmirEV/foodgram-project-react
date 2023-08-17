from django_filters.rest_framework import FilterSet, filters
from rest_framework.filters import SearchFilter
from recipes.models import Ingredient, Recipe, Tag, User


class IngredientFilter(SearchFilter):
    """ Фильтр для ингредиентов. """
    search_param = 'name'

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
