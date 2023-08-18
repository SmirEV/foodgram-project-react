import json
import os
import urllib.request

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.management import BaseCommand
from recipes.models import Ingredient, Recipe, RecipeIngredient, Tag, User

TABLES_DICT = {
    Ingredient: 'ingredients.json',
    Tag: 'tags.json',
    Recipe: 'recipes.json'
}


class Command(BaseCommand):
    help = 'Load data from file'

    def handle(self, *args, **kwargs):
        user = User.objects.create_user(
            email='email@test.ru',
            username='test',
            first_name='test',
            last_name='testtest',
            password='testpassword')

        for model, file in TABLES_DICT.items():
            with open(f'{settings.FILE_DIR}/{file}',
                      'r',
                      encoding='utf-8-sig') as f:
                datas = json.loads(f.read())
                if model == Recipe:
                    for data in datas:
                        image_url = data.pop('image')
                        response = urllib.request.urlopen(image_url)
                        image_content = response.read()
                        image_name = os.path.basename(image_url)
                        image_file = ContentFile(image_content,
                                                 name=image_name)

                        ingredients_data = data.pop('ingredients')
                        for ing in ingredients_data:
                            ing.update({"id": Ingredient.objects.get(
                                name=ing['name']).id})
                            ing.pop('name')

                        tags_data = data.pop('tags')

                        recipe = Recipe.objects.create(
                            **data, author=user)
                        recipe.tags.set(tags_data)
                        recipe.image.save(image_name, image_file)

                        ingredient_list = []
                        for ingredient_data in ingredients_data:
                            ingredient_list.append(
                                RecipeIngredient(
                                    ingredient=Ingredient.objects.get(
                                        id=ingredient_data.pop('id')),
                                    amount=ingredient_data.pop('amount'),
                                    recipe=recipe))
                        RecipeIngredient.objects.bulk_create(ingredient_list)
                else:
                    for data in datas:
                        model.objects.get_or_create(**data)
                print(f'{file} successfully imported.')
        print('Import from json file is complete.')
