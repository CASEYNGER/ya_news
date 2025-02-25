from datetime import datetime, timedelta

import pytest

from django.conf import settings
from django.test.client import Client
from django.urls import reverse
from django.utils import timezone

from news.models import Comment, News


@pytest.fixture(autouse=True)
def enable_db_access_for_all_tests(db):
    """Дает доступ к БД перед каждым тестом."""
    pass


@pytest.fixture
def author(django_user_model):
    """Создаем пользователя-автора."""
    return django_user_model.objects.create(username='Лев Толстой')


@pytest.fixture
def author_client(author):
    """Создаем автора новости."""
    client = Client()
    client.force_login(author)
    return client


@pytest.fixture
def news():
    """Создаем объект новости."""
    return News.objects.create(
        title='Заголовок',
        text='Текст новости',
        date=datetime.today()
    )


@pytest.fixture
def news_list():
    """Создаем список новостей."""
    today = datetime.today()
    return News.objects.bulk_create(
        News(
            title=f'Новость {index}',
            text='Просто текст.',
            date=today - timedelta(days=index)
        )
        for index in range(settings.NEWS_COUNT_ON_HOME_PAGE + 1)
    )


@pytest.fixture
def comment(author, news):
    """Создаем объект комментария."""
    return Comment.objects.create(
        news=news,
        author=author,
        text='Здесь написано что-то интересное!'
    )


@pytest.fixture
def comment_list(author, news):
    """Создаем список комментариев."""
    now = timezone.now()
    comment_list = []
    for index in range(10):
        comment = Comment.objects.create(
            news=news,
            author=author,
            text=f'Текст {index}'
        )
        comment.created = now + timedelta(days=index)
        comment.save()
        comment_list.append(comment)


@pytest.fixture
def home_url():
    """Главная страница."""
    return reverse('news:home')


@pytest.fixture
def detail_url(news):
    """Страница новости."""
    return reverse('news:detail', args=(news.id,))


@pytest.fixture
def delete_url(comment):
    """Удаление."""
    return reverse('news:delete', args=(comment.id,))


@pytest.fixture
def edit_url(comment):
    """Редактирование."""
    return reverse('news:edit', args=(comment.id,))


@pytest.fixture
def login_url():
    """Логин."""
    return reverse('users:login')


@pytest.fixture
def logout_url():
    """Логаут."""
    return reverse('users:logout')


@pytest.fixture
def signup_url():
    """Регистрация."""
    return reverse('users:signup')
