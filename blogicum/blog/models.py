from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Location(models.Model):
    name = models.CharField(
        max_length=256, null=False, blank=False,
        verbose_name='Название места'
    )
    is_published = models.BooleanField(
        default=True, null=False, blank=False, verbose_name='Опубликовано',
        help_text='Снимите галочку, чтобы скрыть публикацию.'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        null=False, blank=False, verbose_name='Добавлено'
    )

    class Meta:
        verbose_name = 'местоположение'
        verbose_name_plural = 'Местоположения'


class Category(models.Model):
    title = models.CharField(
        max_length=256, null=False, blank=False, verbose_name='Заголовок'
    )
    description = models.TextField(
        null=False, blank=False, verbose_name='Описание'
    )
    slug = models.SlugField(
        blank=False, unique=True, verbose_name='Идентификатор',
        help_text=('Идентификатор страницы для URL; '
                   'разрешены символы латиницы, цифры, дефис и подчёркивание.')
    )
    is_published = models.BooleanField(
        default=True, null=False, blank=False, verbose_name='Опубликовано',
        help_text='Снимите галочку, чтобы скрыть публикацию.'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        null=False, blank=False, verbose_name='Добавлено'
    )

    class Meta:
        verbose_name = 'категория'
        verbose_name_plural = 'Категории'


class Post(models.Model):
    title = models.CharField(
        max_length=256, null=False, blank=False, verbose_name='Заголовок'
    )
    text = models.TextField(null=False, blank=False, verbose_name='Текст')
    pub_date = models.DateTimeField(
        null=False, blank=False, verbose_name='Дата и время публикации',
        help_text=('Если установить дату и время в будущем —'
                   ' можно делать отложенные публикации.')
    )
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, null=False,
        blank=False, verbose_name='Автор публикации'
    )
    location = models.ForeignKey(
        Location, on_delete=models.SET_NULL, null=True, blank=True,
        verbose_name='Местоположение'
    )
    category = models.ForeignKey(
        Category, on_delete=models.SET_NULL, null=True,
        blank=False, verbose_name='Категория'
    )
    is_published = models.BooleanField(
        default=True, null=False,
        blank=False, verbose_name='Опубликовано',
        help_text='Снимите галочку, чтобы скрыть публикацию.'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        null=False, blank=False,
        verbose_name='Добавлено'
    )

    image = models.ImageField('Фото', upload_to='posts_images', blank=True)

    class Meta:
        verbose_name = 'публикация'
        verbose_name_plural = 'Публикации'


class Comment(models.Model):
    text = models.TextField('Текст комментария')
    post = models.ForeignKey(
        'Post',
        on_delete=models.CASCADE,
        related_name='comments',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='comments',
    )
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)

    class Meta:
        ordering = ('created_at',)
        verbose_name = 'Комментарий'
        verbose_name_plural = 'Комментарии'

    def __str__(self):
        return f'Комментарий {self.id} к посту {self.post_id}'
