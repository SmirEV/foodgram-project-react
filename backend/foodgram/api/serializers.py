from rest_framework import serializers

from recipes.models import (Tag, Ingredient,
                            Recipe, RecipeIngredient,
                            User)


class TagSerializer(serializers.ModelSerializer):

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


class UserSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('id', 'email', 'username',
                  'first_name', 'last_name',
                  'is_subscribed')

    def get_is_subscribed(self, obj):
        return False


class RecipeSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True)
    ingredients = serializers.SerializerMethodField()
    author = UserSerializer()

    class Meta:
        model = Recipe
        fields = '__all__'

    def get_ingredients(self, instance):
        return RecipeIngredientSerializer(
            instance.recipe_ingredients.all(),
            many=True
        ).data


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
