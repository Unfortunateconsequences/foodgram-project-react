from django.db import models
from users.models import MyUser


class Tag(models.Model):

    ...


class Ingredient(models.Model):

    ...


class Recipe(models.Model):

    author = models.ForeignKey(
        MyUser,
        on_delete=models.CASCADE,
        related_name='recipes'
    )


class Favorites(models.Model):

    ...
