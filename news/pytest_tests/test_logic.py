import pytest

from http import HTTPStatus

from django.urls import reverse

from pytest_django.asserts import assertRedirects, assertFormError

from news.forms import BAD_WORDS, WARNING
from news.models import Comment


# Метка, что все тесты требуют доступ к БД
pytestmark = pytest.mark.django_db


def test_anonymous_user_cant_create_comment(client, new_comment, news):
    """Тест доступа для отправки комментария анонимного пользователя."""
    # Получаем адрес
    url = reverse('news:detail', args=(news.id,))
    # Выполняем запрос
    client.post(url, data=new_comment)
    assert Comment.objects.count() == 0


def test_auth_user_can_create_comment(
        author_client, author, new_comment, news
):
    """Тест доступа для отправки комментария авторизированного пользователя."""
    # Получаем адрес
    url = reverse('news:detail', args=(news.id,))
    # Выполняем запрос
    author_client.post(url, data=new_comment)
    # Проверяем, что комментарий добавлен
    assert Comment.objects.count() == 1
    # Выполняем запрос, получаем новый текст комментария
    new_cmnt = Comment.objects.get()
    # Сверяем атрибуты с ожидаемыми
    assert new_cmnt.text == new_comment['text']
    assert new_cmnt.news == news
    assert new_cmnt.author == author


def test_user_cant_use_bad_words(author_client, news):
    """Тест на использование стоп-слов."""
    bad_words = {'text': f'Какой-то текст, {BAD_WORDS[0]}, ...'}
    # Получаем адрес
    url = reverse('news:detail', args=(news.id,))
    # Выполняем запрос
    response = author_client.post(url, data=bad_words)
    # Проверяем, что форма не вернула ошибку...
    assertFormError(
        response,
        form='form',
        field='text',
        errors=WARNING
    )
    # Считаем комментарии, если 0 - то запретных слов нет
    comments_count = Comment.objects.count()
    assert comments_count == 0


def test_auth_user_can_edit_comment(author_client, new_comment, news, comment):
    """
    Тест на доступ к редактированию авторизованным
    пользователем своего комментария.
    """
    # Получаем адрес
    url = reverse('news:detail', args=(news.id,))
    # Получаем адрес к комментариям
    url_to_comments = reverse('news:edit', args=(comment.id,))
    # Выполняем запрос
    response = author_client.post(url_to_comments, data=new_comment)
    assertRedirects(response, url + '#comments')
    # Обновляем в БД и проверяем
    comment.refresh_from_db()
    assert comment.text == new_comment['text']


def test_auth_user_can_delete_comment(author_client, news, comment):
    """
    Тест на доступ к удалению авторизованным
    пользователем своего комментария.
    """
    # Получаем адрес
    url = reverse('news:detail', args=(news.id,))
    # Получаем адрес к комментариям
    url_to_comments = reverse('news:delete', args=(comment.id,))
    # Выполняем запрос
    response = author_client.delete(url_to_comments)
    assertRedirects(response, url + '#comments')
    # Если количество комментариев - 0, то комментарий удален
    comments_count = Comment.objects.count()
    assert comments_count == 0


def test_auth_user_cant_edit_comment_of_another_user(
        author_client, new_comment, comment
):
    """
    Тест на запрет доступа к редактирования авторизованным
    пользователем чужого комментария.
    """
    # Получаем адрес
    url_to_comment = reverse('news:detail', args=(comment.id,))
    # Выполняем запрос
    response = author_client.post(url_to_comment, data=new_comment)
    assert response.status_code == HTTPStatus.FOUND
    expected_redirect_url = reverse(
        'news:detail', args=(comment.id,)
    ) + '#comments'
    assert response.url == expected_redirect_url
    comment_from_db = Comment.objects.get(id=comment.id)
    assert comment.text == comment_from_db.text
    assert comment.news == comment_from_db.news
    assert comment.author == comment_from_db.author


def test_auth_user_cant_delete_comment_of_another_user(
        author_client, comment
):
    """
    Тест на запрет доступа к удалению авторизованным
    пользователем чужого комментария.
    """
    # Получаем адрес
    url_to_comment = reverse('news:detail', args=(comment.id,))
    # Выполняем запрос
    response = author_client.delete(url_to_comment)
    assert response.status_code == HTTPStatus.METHOD_NOT_ALLOWED
    comments_count = Comment.objects.count()
    assert comments_count == 1
