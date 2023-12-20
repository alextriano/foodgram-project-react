import csv

from django.core.management.base import BaseCommand

from recipes.models import Ingredient


class Command(BaseCommand):
    help = 'Загрузка ингредиентов в базу данных.'

    def handle(self, *args, **options):
        ingredients_list = []
        file_path = 'data/ingredients.csv'
        with open(file_path, 'r', encoding='utf-8') as file:
            csv_reader = csv.DictReader(file)
            for row in csv_reader:
                ingredient = Ingredient(
                    name=row['абрикосовое варенье'],
                    measurement_unit=row['г']
                )
                ingredients_list.append(ingredient)
            Ingredient.objects.bulk_create(ingredients_list)

        self.stdout.write(
            self.style.SUCCESS('Данные успешно загружены.'))
