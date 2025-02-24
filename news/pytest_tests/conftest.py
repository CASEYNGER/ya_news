from datetime import datetime, timedelta

import pytest

from django.conf import settings
from django.test.client import Client
from django.utils import timezone

from news.models import Comment, News


@pytest.fixture
def author(django_user_model):
    """Создаем пользователя-автора."""
    return django_user_model.objects.create(username='Лев Толстой')


@pytest.fixture
def author_client(author):
    """Создаем автора новости."""
    # Создаем новый экземпляр клиента, чтобы не менять глобальный
    client = Client()
    # Логиним автора
    client.force_login(author)
    return client


@pytest.fixture
def news():
    """Создаем объект новости."""
    news = News.objects.create(
        title='Заголовок',
        text='Текст новости',
        date=datetime.today()
    )
    return news


@pytest.fixture
def news_list():
    """Создаем список новостей."""
    # Получаем сегодняшнюю дату
    today = datetime.today()
    # Создаем список
    news_list = News.objects.bulk_create(
        News(
            title=f'Новость {index}',
            text='Бла-бла-бла.',
            date=today - timedelta(days=index)
        )
        for index in range(settings.NEWS_COUNT_ON_HOME_PAGE + 1)
    )
    return news_list


@pytest.fixture
def comment(author, news):
    """Создаем объект комментария."""
    comment = Comment.objects.create(
        news=news,
        author=author,
        text='Здесь написано что-то интересное!'
    )
    return comment


@pytest.fixture
def comment_list(author, news):
    """Создаем список комментариев."""
    # Получаем сегодняшнее время
    now = timezone.now()
    # Создаем пустой список, который будет наполняться
    comment_list = []
    for index in range(2):
        comment = Comment.objects.create(
            news=news,
            author=author,
            text=f'Текст {index}'
        )
        # Время создания комментария
        comment.created = now + timedelta(days=index)
        # Сохраняем комментарий
        comment.save()
        # Добавляем комментарий в список
        comment_list.append(comment)
        return comment_list
