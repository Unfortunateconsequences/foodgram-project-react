from django.db import models
from django.contrib.auth.models import AbstractUser


class MyUser(AbstractUser):

    email = models.EmailField(
        verbose_name='Адрес электронной почты',
        unique=True
    )
    username = models.CharField(
        verbose_name='Уникальный юзернейм',
        unique=True
    )
    first_name = models.CharField(
        verbose_name='Имя'
    )
    last_name = models.CharField(
        verbose_name='Фамилия'
    )
    password = models.CharField(
        verbose_name='Пароль'
    )
    is_active = models.BooleanField(
        verbose_name='Активен',
        default=True
    )

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ('username',)


class Subscriptions(models.Model):

    user = models.ForeignKey(
        MyUser,
        related_name='subscriber',
        on_delete=models.CASCADE,
        verbose_name="Подписчик",
    )
    author = models.ForeignKey(
        MyUser,
        related_name='author',
        on_delete=models.CASCADE,
        verbose_name="Автор публикации",
    )

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
