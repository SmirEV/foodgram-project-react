import webcolors
from drf_extra_fields.fields import Base64ImageField
from recipes.models import (Favorites, Ingredient, MyShoppingCart, Recipe,
                            RecipeIngredient, Subscribtions, Tag, User)
from rest_framework import serializers


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
        user = self.context.get('request').user
        if user.is_anonymous:
            return False
        return Subscribtions.objects.filter(
            user=user, author=instance.id).exists()


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


class FavoritesSerializer(serializers.ModelSerializer):
    """
    Сериализатор для избранного.
    """
    id = serializers.IntegerField(source='recipe.id')
    name = serializers.CharField(source='recipe.name')
    image = Base64ImageField(source='recipe.image')
    cooking_time = serializers.IntegerField(source='recipe.cooking_time')

    class Meta:
        model = Favorites
        fields = ('id', 'name', 'image', 'cooking_time')

    def validate(self, data):
        """ Проверка данных на уровне сериализатора. """
        user_id = data['user_id']
        recipe_id = data['recipe_id']
        if Favorites.objects.filter(
                user=user_id,
                recipe=recipe_id).exists():
            raise serializers.ValidationError({
                'errors': 'Ошибка! Рецепт уже добавлен в избранное.'})
        data['user'] = User.objects.get(User, id=user_id)
        data['recipe'] = Recipe.objects.get(Recipe, id=recipe_id)
        return data
#
#
# class FavoritesSerializer(serializers.ModelSerializer):
#    """ Сериализатор избранных рецептов. """
#
#    image = Base64ImageField()
#
#    class Meta:
#        model = Recipe
#        fields = ('id', 'name', 'image', 'cooking_time')
#        read_only_fields = ('id', 'name', 'image', 'cooking_time')


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


class RecipeSerializer(serializers.ModelSerializer):
    """ Сериализатор рецептов. """
    tags = TagSerializer(many=True)
    ingredients = serializers.SerializerMethodField()
    author = AuthorSerializer()
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    image = Base64ImageField(max_length=None)

    class Meta:
        model = Recipe
        fields = ('tags', 'id', 'ingredients', 'author',
                  'is_favorited', 'image', 'is_in_shopping_cart',
                  'name', 'text', 'cooking_time')

    def get_ingredients(self, instance):
        return RecipeIngredientSerializer(
            instance.recipe_ingredients.all(),
            many=True
        ).data

    def get_is_favorited(self, obj):
        """ Проверка рецепта в списке избранного. """
        user = self.context.get('request').user
        if user.is_anonymous:
            return False
        return Favorites.objects.filter(
            recipe=obj,
            user=user).exists()

    def get_is_in_shopping_cart(self, obj):
        """ Проверка рецепта в корзине покупок. """
        user = self.context.get('request').user
        if not user or user.is_anonymous:
            return False
        return MyShoppingCart.objects.filter(
            recipe=obj,
            user=user).exists()


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
        many=True,)
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

    def get_author(self, instance):
        return AuthorSerializer(instance.author).data

    def to_representation(self, instance):
        return RecipeSerializer(instance, context={
            'request': self.context.get('request')
        }).data


class SubscribeSerializer(serializers.ModelSerializer):
    """
    Сериализатор для подписчика.
    """
    id = serializers.IntegerField(source='author.id')
    email = serializers.EmailField(source='author.email')
    username = serializers.CharField(source='author.username')
    first_name = serializers.CharField(source='author.first_name')
    last_name = serializers.CharField(source='author.last_name')
    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Subscribtions
        fields = ('id', 'email', 'username', 'first_name', 'last_name',
                  'is_subscribed', 'recipes', 'recipes_count',)
        read_only_fields = ('is_subscribed', 'recipes_count',)

    def validate(self, data):
        """ Проверка данных на уровне сериализатора. """
        user_id = data['user_id']
        author_id = data['author_id']
        if user_id == author_id:
            raise serializers.ValidationError({
                'errors': 'Ошибка подписки! Нельзя подписаться на самого себя.'
            })
        if Subscribtions.objects.filter(
                user=user_id,
                author=author_id).exists():
            raise serializers.ValidationError({
                'errors': 'Ошибка подписки! Нельзя подписаться повторно.'
            })
        data['user'] = User.objects.get(User, id=user_id)
        data['author'] = User.objects.get(User, id=author_id)
        return data

    def get_is_subscribed(self, obj):
        """ Проверка подписки. """
        return Subscribtions.objects.filter(
            user=obj.user, author=obj.author).exists()

    def get_recipes(self, obj):
        """ Получение рецептов автора. """
        request = self.context.get('request')
        recipes_limit = request.GET.get('recipes_limit')
        recipes = Recipe.objects.filter(author=obj.author)
        if recipes_limit:
            recipes = recipes[:int(recipes_limit)]
        serializer = RecipeShortSerializer(recipes, many=True)
        return serializer.data

    def get_recipes_count(self, obj):
        """ Подсчет рецептов автора. """
        return Recipe.objects.filter(author=obj.author).count()
