from http import HTTPStatus

import pytest

from django.urls import reverse

from pytest_django.asserts import assertRedirects


# Метка, что все тесты требуют доступ к БД
pytestmark = pytest.mark.django_db


@pytest.mark.parametrize(
    # Имя параметра функции
    'name',
    # Значения, которые будут передаваться в name
    ('news:home', 'users:login', 'users:logout', 'users:signup'),
)
def test_pages_availability_for_anonymous_user(client, name):
    """
    Тест доступа анонимному пользователю:

    - Главной страницы,
    - Страниц входа и выхода из учетной записи,
    - Страницы регистрации.
    """
    # Получаем ссылку на нужный адрес
    url = reverse(name)
    # Выполняем запрос
    response = client.get(url)
    assert response.status_code == HTTPStatus.OK


def test_detail_news_page_for_anonymous_user(client, news):
    """
    Тест доступа анонимному пользователю:

    - Страницы отдельной новостной страницы.
    """
    # Получаем ссылку на нужный адрес
    url = reverse('news:detail', args=(news.id,))
    # Выполняем запрос
    response = client.get(url)
    assert response.status_code == HTTPStatus.OK


@pytest.mark.parametrize(
    'parametrized_client, expected_status',
    # Предварительно оборачиваем имена фикстур
    # в вызов функции pytest.lazy_fixture()
    (
        (pytest.lazy_fixture('admin_client'), HTTPStatus.NOT_FOUND),
        (pytest.lazy_fixture('author_client'), HTTPStatus.OK)
    ),
)
@pytest.mark.parametrize(
    'name',
    ('news:delete', 'news:edit'),
)
def test_delete_and_edit_comments_availability_for_author_and_other(
    parametrized_client, expected_status, name, comment
):
    """
    Тест доступа автора новости к удалению
    и редактированию своих комментариев.

    Авторизованный пользователь не может иметь доступа
    к редактированию и удалению чужих комментариев.
    """
    # Получаем ссылку на нужный адрес
    url = reverse(name, args=(comment.id,))
    # Выполняем запрос от имени клиента parametrized_client
    response = parametrized_client.get(url)
    # Ожидаем ответ страницы, указанный в expected_status
    assert response.status_code == expected_status


@pytest.mark.parametrize(
    'name',
    ('news:edit', 'news:delete'),
)
def test_redirect_for_anonymous_user_after_try_delete_or_edit_comment(
    client, name, comment
):
    """
    Тест редиректа при попытке зайти анонимным пользователем
    на страницу удаления или редактирования комментария.
    """
    # Получаем URL входа
    login_url = reverse('users:login')
    # Получаем ссылку на нужный адрес
    url = reverse(name, args=(comment.id,))
    # Ожидаемый адрес
    expected_url = f'{login_url}?next={url}'
    # Выполняем запрос
    response = client.get(url)
    assertRedirects(response, expected_url)
