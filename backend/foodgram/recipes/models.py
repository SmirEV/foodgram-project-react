from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Tag(models.Model):
    name = models.CharField(max_length=200)
    color = models.CharField(max_length=7)
    slug = models.SlugField(max_length=200, unique=True)

class Recipe(models.Model):
    tags = models.ManyToManyField(Tag)
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    # ingredients =
    # is_favorite =
    # is_in_shopping_cart =
    name =models.CharField(max_length=200)
    # image =
    text = models.TextField()
    #можно добавить валидацию?
    cooking_time = models.PositiveIntegerField()
