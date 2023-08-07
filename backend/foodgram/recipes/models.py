from django.db import models
from django.contrib.auth import get_user_model
from django.db.models import F, Q, CheckConstraint, UniqueConstraint 

User = get_user_model()


class Tag(models.Model):
    name = models.CharField(max_length=200)
    color = models.CharField(max_length=7)
    slug = models.SlugField(max_length=200, unique=True)


class Recipe(models.Model):
    tags = models.ManyToManyField(
        Tag,
        blank=False)
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE)
    ingredients = models.ManyToManyField(
        'Ingredient',
        through='RecipeIngredient',
        through_fields=('recipe', 'ingredient'),
        blank=False
        )
    is_favorite = models.BooleanField()
    is_in_shopping_cart = models.BooleanField()
    name = models.CharField(
        max_length=200,
        blank=False,
        null=False)
    image = models.ImageField(
        upload_to='images/',
        # default='no_photo.jpg',
        blank=False,
        null=False)
    text = models.TextField(
        blank=False,
        null=False)
    # можно добавить валидацию?
    cooking_time = models.PositiveIntegerField(
        blank=False,
        null=False)


class Ingredient(models.Model):
    name = models.CharField(max_length=200)
    measurement_unit = models.CharField(max_length=200)


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        related_name='recipe_ingredients',
        on_delete=models.CASCADE)
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE)
    amount = models.PositiveIntegerField()


class IsSubscribed(models.Model):
    """Модель для работы с подписками."""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower',
        verbose_name='Подписчик'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following',
        verbose_name='Автор'
    )

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        constraints = [
            CheckConstraint(name='not_same', check=~Q(user=F('author'))),
            UniqueConstraint(
                fields=['user', 'author'],
                name='unique_following'),
        ]


class Favorites(models.Model):
    """Модель для работы с избранным."""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='user',
        verbose_name='Пользователь'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='favorite_recipe',
        verbose_name='Рецепт'
    )

    class Meta:
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное'

        constraints = [
            UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_favorites'),
        ]


class MyShoppingCart(models.Model):
    """Модель для работы с корзиной."""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='cooker',
        verbose_name='Покупатель'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='for_cooking',
        verbose_name='Рецепт'
    )

    class Meta:
        verbose_name = 'Корзина'
        verbose_name_plural = 'Корзина'
        constraints = [
            UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_shoppingcart'),
        ]
