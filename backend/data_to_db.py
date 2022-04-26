import csv
import os

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "foodgram.settings")
django.setup()

from recipes.models import Ingredient, Tag

with open('../data/ingredients.csv') as f:
    reader = csv.reader(f)
    for name, measurement_unit in reader:
        if not Ingredient.objects.filter(name=name).exists():
            Ingredient.objects.create(name=name, measurement_unit=measurement_unit)

with open('../data/tags.csv') as f:
    reader = csv.reader(f)
    for name, color, slug in reader:
        Tag.objects.create(name=name, color=color, slug=slug)
