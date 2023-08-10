import webcolors

from rest_framework import serializers
from drf_extra_fields.fields import Base64ImageField

from recipes.models import (Tag, Ingredient,
                            Recipe, RecipeIngredient,
                            User, IsSubscribed,
                            Favorites, MyShoppingCart)


class NameToHexColor(serializers.Field):
    def to_representation(self, value):
        return value

    def to_internal_value(self, data):
        try:
            data = webcolors.name_to_hex(data)
        except ValueError:
            raise serializers.ValidationError('Неизвестный цвет')
        return data


class TagSerializer(serializers.ModelSerializer):
    color = NameToHexColor()

    class Meta:
        model = Tag
        fields = ('id', 'name', 'color', 'slug')


class IngredientSerializer(serializers.ModelSerializer):

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class RecipeIngredientSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all()
    )
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount',)


class UserCreateSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ('id', 'email', 'username',
                  'first_name', 'last_name')


class AuthorSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('email', 'id', 'username',
                  'first_name', 'last_name',
                  'is_subscribed')

    def get_is_subscribed(self, instance):
        request = self.context.get('request')
        print(request)
        user = request.user
        return len(IsSubscribed.objects.all().filter(
            author=instance.id,
            user=user)) == 1


class AuthorWithRecipesSerializer(AuthorSerializer):
    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('id', 'email', 'username',
                  'first_name', 'last_name',
                  'is_subscribed', 'recipes',
                  'recipes_count')

    def get_recipes(self, instance):
        request = self.context.get('request')
        recipes = Recipe.objects.all()
        return RecipeShortSerializer(recipes,
                                     many=True).data

    def get_recipes_count(self, instance):
        return instance.recipes.count()


class RecipeSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True)
    ingredients = serializers.SerializerMethodField()
    author = AuthorSerializer()
    is_favorite = serializers.SerializerMethodField()
    image = Base64ImageField(max_length=None)

    class Meta:
        model = Recipe
        fields = '__all__'

    def get_ingredients(self, instance):
        return RecipeIngredientSerializer(
            instance.recipe_ingredients.all(),
            many=True
        ).data

    def get_is_favorite(self, instance):
        request = self.context.get('request')
        user = request.user
        return len(Favorites.objects.all().filter(
            recipe=instance.id,
            user=user)) == 1


class RecipeShortSerializer(RecipeSerializer):

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class RecipeCreateSerializer(serializers.ModelSerializer):
    '''
    Надо прикрутить теги и картинки
    '''
    tags = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Tag.objects.all())
    ingredients = RecipeIngredientSerializer(many=True)
    author = serializers.SerializerMethodField()
    image = Base64ImageField(max_length=None)

    class Meta:
        model = Recipe
        fields = ('id', 'tags', 'author',
                  'ingredients', 'name', 'image',
                  'text', 'cooking_time')

    def create(self, validated_data):
        ingredients_data = validated_data.pop('ingredients')
        tags_data = validated_data.pop('tags')
        print(f'\n\n{ingredients_data}\n\n')
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags_data)
        ingredient_list = []
        for ingredient_data in ingredients_data:
            ingredient_list.append(
                RecipeIngredient(
                    ingredient=ingredient_data.pop('id'),
                    amount=ingredient_data.pop('amount'),
                    recipe=recipe,
                )
            )
        RecipeIngredient.objects.bulk_create(ingredient_list)
        return recipe

    def get_author(self, instance):
        return AuthorSerializer(instance.author).data

    def to_representation(self, instance):
        return RecipeSerializer(instance, context={
            'request': self.context.get('request')
        }).data


class FavoritesSerializer(serializers.ModelSerializer):
    """  Сериализатор избранных рецептов """

    class Meta:
        model = Favorites
        fields = ('user', 'recipe',)

    def to_representation(self, instance):
        return RecipeShortSerializer(
            instance.recipe,
            context={'request': self.context.get('request')}
        ).data


class ShoppingCartSerializer(serializers.ModelSerializer):
    """Сериализатор для списка покупок """

    class Meta:
        model = MyShoppingCart
        fields = ('user', 'recipe',)

    def to_representation(self, instance):
        return RecipeShortSerializer(
            instance.recipe,
            context={'request': self.context.get('request')}
        ).data
