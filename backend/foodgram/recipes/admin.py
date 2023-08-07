from django.contrib import admin

from recipes.models import (Tag, Recipe, Ingredient,
                            RecipeIngredient, IsSubscribed,
                            Favorites, MyShoppingCart)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    pass


class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredient
    extra = 1


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    inlines = (RecipeIngredientInline, )


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    pass


@admin.register(IsSubscribed)
class IsSubscribedAdmin(admin.ModelAdmin):
    pass


@admin.register(Favorites)
class FavoritesAdmin(admin.ModelAdmin):
    pass


@admin.register(MyShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    pass
