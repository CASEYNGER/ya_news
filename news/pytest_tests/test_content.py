import pytest

from http import HTTPStatus

from django.conf import settings
from django.urls import reverse


# Метка, что все тесты требуют доступ к БД
pytestmark = pytest.mark.django_db


def test_count_news_on_home_page(client, news_list):
    """Тест на количество новостей на главной странице."""
    # Получаем адрес
    url = reverse('news:home')
    # Выполняем запрос
    response = client.get(url)
    # Получаем список данных из контекста по ключу 'object_list'
    object_list = response.context['object_list']
    # Считаем полученный список данных
    news_count = object_list.count()
    # Проверяем, что длина списка данных равна константе в настройках
    assert news_count == settings.NEWS_COUNT_ON_HOME_PAGE


def test_sorted_news(client, news_list):
    """Тест на правильную сортировку новостей (от новых к старым)."""
    # Получаем адрес
    url = reverse('news:home')
    # Выполняем запрос
    response = client.get(url)
    # Получаем список данных из контекста по ключу 'object_list'
    object_list = response.context['object_list']
    # Получаем даты новостей в том порядке, как они выведены на странице
    all_dates = [news.date for news in object_list]
    # Сортируем даты новостей от самых свежих до самых старых
    sorted_dates = sorted(all_dates, reverse=True)
    # Проверяем сортировку
    assert all_dates == sorted_dates


def test_comments_order(client, news, comment_list):
    """Тест на правильную сортировку комментариев (от новых к старым)."""
    # Получаем адрес
    url = reverse('news:detail', args=(news.id,))
    # Выполняем запрос
    response = client.get(url)
    # Проверяем, что объект новости находится в словаре
    # контекста под ожидаемым именем
    assert 'news' in response.context
    # Получаем объект новости
    news = response.context['news']
    # Получаем все комментарии к новости
    all_comments = news.comment_set.all()
    # Собираем временные метки всех комментариев
    all_timestamps = [comment.created for comment in all_comments]
    # Сортируем временные метки, менять порядок сортировки не надо
    sorted_timestamps = sorted(all_timestamps)
    assert all_timestamps == sorted_timestamps


@pytest.mark.parametrize(
    'parametrized_client, expected_status',
    (
        (pytest.lazy_fixture('client'), HTTPStatus.NOT_FOUND),
        (pytest.lazy_fixture('author_client'), HTTPStatus.OK),
    ),
)
def test_authorized_client_has_form_and_anonymous_client_has_no_form(
    parametrized_client,
    expected_status,
    comment
):
    """
    Тест доступа для отправки комментария
    авторизованному пользователю.

    Тест запрета доступа для отправки комментария
    анонимному пользователю.
    """
    # Получаем адрес
    url = reverse('news:detail', args=(comment.id,))
    # Выполняем запрос
    response = parametrized_client.get(url)
    # Если ожидаемый статус ожидался 404, форма не должна быть в контексте
    if expected_status == HTTPStatus.NOT_FOUND:
        assert 'form' not in response.context
    # Если статус ожидался 200, форма должна быть в контексте
    else:
        assert 'form' in response.context
