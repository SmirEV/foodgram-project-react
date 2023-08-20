import webcolors
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers

from recipes.models import (Favorites, Ingredient, IsSubscribed,
                            MyShoppingCart, Recipe, RecipeIngredient, Tag,
                            User)


class NameToHexColor(serializers.Field):
    """ Класс для перевода именованных цветов в 16-е представление. """
    def to_representation(self, value):
        return value

    def to_internal_value(self, data):
        try:
            data = webcolors.name_to_hex(data)
        except ValueError:
            raise serializers.ValidationError('Неизвестный цвет')
        return data


class TagSerializer(serializers.ModelSerializer):
    """ Сериализатор тегов. """
    color = NameToHexColor()

    class Meta:
        model = Tag
        fields = ('id', 'name', 'color', 'slug')


class IngredientSerializer(serializers.ModelSerializer):
    """ Сериализатор ингредиентов. """

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class RecipeIngredientSerializer(serializers.ModelSerializer):
    """ Сериализатор ингредиентов для рецептов. """
    # id = serializers.ReadOnlyField(source='ingredient.id')
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
    """ Сериализатор для создания пользователя. """

    class Meta:
        model = User
        fields = ('id', 'email', 'username',
                  'first_name', 'last_name', 'password')

    def create(self, validated_data):
        username = validated_data.pop('username')
        first_name = validated_data.pop('first_name')
        last_name = validated_data.pop('last_name')
        email = validated_data.pop('email')
        password = validated_data.pop('password')

        user = User.objects.create_user(
            username=username,
            first_name=first_name,
            last_name=last_name,
            email=email,
            password=password)
        user.save()

        return user


class AuthorSerializer(serializers.ModelSerializer):
    """ Сериализатор авторов рецептов. """
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('email', 'id', 'username',
                  'first_name', 'last_name',
                  'is_subscribed')

    def get_is_subscribed(self, instance):
        request = self.context.get('request')
        user = request.user
        return (user.is_authenticated
                and IsSubscribed.objects.all().
                filter(author=instance.id, user=user).exists())


class AuthorWithRecipesSerializer(AuthorSerializer):
    """ Сериализатор авторов с их рецептами и их количеством. """
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
        recipes = instance.recipe_set.all()
        return RecipeShortSerializer(recipes,
                                     many=True).data

    def get_recipes_count(self, instance):
        return instance.recipe_set.all().count()


class RecipeSerializer(serializers.ModelSerializer):
    """ Сериализатор рецептов. """
    tags = TagSerializer(many=True)
    ingredients = serializers.SerializerMethodField()
    #ingredients = RecipeIngredientSerializer(
    #    many=True,
    #    read_only=True,
    #    source='recipe_ingredients'
    #)
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
        if user.is_authenticated:
            return Favorites.objects.all().filter(
                recipe=instance.id, user=user).exists()
        return False


class RecipeShortSerializer(RecipeSerializer):
    """ Сериализатор для вывода рецептов в укороченном формате. """

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class RecipeCreateSerializer(serializers.ModelSerializer):
    """ Сериализатор для создания рецептов. """
    tags = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Tag.objects.all())
    ingredients = RecipeIngredientSerializer(
        many=True,
        read_only=True,
        #source='recipe_ingredients'
    )
    author = serializers.SerializerMethodField()
    image = Base64ImageField(max_length=None)

    class Meta:
        model = Recipe
        fields = ('id', 'tags', 'author',
                  'ingredients', 'name', 'image',
                  'text', 'cooking_time')

    @staticmethod
    def create_ingredients_list(recipe, ingredients_data):
        ingredient_list = [
            RecipeIngredient(
                ingredient=ingredient_data.pop('id'),
                amount=ingredient_data.pop('amount'),
                recipe=recipe) for ingredient_data in ingredients_data]
        RecipeIngredient.objects.bulk_create(ingredient_list)

    def create(self, validated_data):
        ingredients_data = validated_data.pop('ingredients')
        tags_data = validated_data.pop('tags')
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags_data)
        self.create_ingredients_list(recipe, ingredients_data)
        return recipe

    def update(self, instance, validated_data):
        instance.tags.clear()
        instance.tags.set(validated_data.pop('tags'))
        RecipeIngredient.objects.filter(recipe=instance).delete()
        ingredients_data = validated_data.pop('ingredients')
        self.create_ingredients_list(instance, ingredients_data)
        return super().update(instance, validated_data)
        # return instance #???

    def get_author(self, instance):
        return AuthorSerializer(instance.author).data

    def to_representation(self, instance):
        return RecipeSerializer(instance, context={
            'request': self.context.get('request')
        }).data


class FavoritesSerializer(serializers.ModelSerializer):
    """ Сериализатор избранных рецептов. """

    class Meta:
        model = Favorites
        fields = ('user', 'recipe',)

    def to_representation(self, instance):
        return RecipeShortSerializer(
            instance.recipe,
            context={'request': self.context.get('request')}
        ).data


class ShoppingCartSerializer(serializers.ModelSerializer):
    """ Сериализатор для списка покупок. """

    class Meta:
        model = MyShoppingCart
        fields = ('user', 'recipe',)

    def to_representation(self, instance):
        return RecipeShortSerializer(
            instance.recipe,
            context={'request': self.context.get('request')}
        ).data
