from django.contrib.auth import get_user_model
from django.db import models
from django.db.models import CheckConstraint, F, Q, UniqueConstraint


User = get_user_model()


class Tag(models.Model):
    """ Модель тегов для рецептов. """
    name = models.CharField(max_length=200)
    color = models.CharField(max_length=20)
    slug = models.SlugField(max_length=200, unique=True)

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    """ Модель ингредиентов для рецептов. """
    name = models.CharField(max_length=200)
    measurement_unit = models.CharField(max_length=20)

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'

    def __str__(self):
        return f'{self.name}, {self.measurement_unit}.'


class Recipe(models.Model):
    """ Модель рецептов. """
    tags = models.ManyToManyField(
        Tag,
        blank=False,
        verbose_name='Тег')
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор')
    ingredients = models.ManyToManyField(
        Ingredient,
        through='RecipeIngredient',
        through_fields=('recipe', 'ingredient'),
        blank=False,
        verbose_name='Ингредиенты')
    is_favorite = models.BooleanField(default=False)
    is_in_shopping_cart = models.BooleanField(default=False)
    name = models.CharField(
        max_length=200,
        blank=False,
        null=False,
        verbose_name='Название')
    image = models.ImageField(
        verbose_name='Ссылка на картинку',
        upload_to='recipes/',
        blank=False,
        null=False)
    text = models.TextField(
        blank=False,
        null=False,
        verbose_name='Способ приготовления')
    cooking_time = models.PositiveIntegerField(
        blank=False,
        null=False,
        verbose_name='Время приготовления (мин)')

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

    def __str__(self):
        return self.name


class RecipeIngredient(models.Model):
    """ Связь ингредиентов и рецептов. """
    recipe = models.ForeignKey(
        Recipe,
        related_name='recipe_ingredients',
        verbose_name='Рецепт',
        on_delete=models.CASCADE)
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        verbose_name='Ингредиент',
        related_name='ingredient')
    amount = models.PositiveIntegerField(
        verbose_name='Количество')


class IsSubscribed(models.Model):
    """ Модель для работы с подписками. """
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
    """ Модель для работы с избранным. """
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
    """ Модель для работы с корзиной. """
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
