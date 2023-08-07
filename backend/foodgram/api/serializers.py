﻿import webcolors

from rest_framework import serializers

from recipes.models import (Tag, Ingredient,
                            Recipe, RecipeIngredient,
                            User, IsSubscribed,
                            Favorites)


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
        fields = '__all__'


class IngredientSerializer(serializers.ModelSerializer):

    class Meta:
        model = Ingredient
        fields = '__all__'


class RecipeIngredientSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit')

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeIngredientCreateSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(
        source='ingredient',
        queryset=Ingredient.objects.all())

    class Meta:
        model = RecipeIngredient
        field = ('id', 'amount')


class UserCreateSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ('id', 'email', 'username',
                  'first_name', 'last_name')


class AuthorSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('id', 'email', 'username',
                  'first_name', 'last_name',
                  'is_subscribed')

    def get_is_subscribed(self, instance):
        request = self.context.get('request')
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
        recipes = Recipe.objects.all().filter(
            author=instance.id)
        return RecipeSerializer(recipes,
                                many=True).data

    def get_recipes_count(self, instance):
        return len(Recipe.objects.all().filter(
            author=instance.id))


class RecipeSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True)
    ingredients = serializers.SerializerMethodField()
    author = AuthorSerializer()
    is_favorite = serializers.SerializerMethodField()

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
    ingredients = RecipeIngredientCreateSerializer(many=True)

    class Meta:
        model = Recipe
        fields = ('name',
                  'cooking_time',
                  'text',
                  'tags',
                  'ingredients')

    def create(self, validated_data):
        ingredients = validated_data.pop('ingredients')
        print(ingredients)
        instance = super().create(validated_data)
        #  тут лучше через bulk_create
        for ingredient_data in ingredients:
            RecipeIngredient(
                recipe=instance,
                ingredient=ingredient_data['ingredient'],
                amount=ingredient_data['amount']
                ).save()
        return instance

    def to_representation(self, instance):
        return super().to_representation(instance)
