from http import HTTPStatus
import random

from pytest_django.asserts import assertRedirects, assertFormError

from news.forms import BAD_WORDS, WARNING
from news.models import Comment

NEW_COMMENT_TEXT = 'Новый текст'


def test_anonymous_user_cant_create_comment(client, detail_url):
    """Аноним не может оставлять комментарий."""
    comment_count_before = Comment.objects.count()
    client.post(detail_url, data={'text': NEW_COMMENT_TEXT})
    comment_count_after = Comment.objects.count()
    assert comment_count_after == comment_count_before


def test_auth_user_can_create_comment(
        author_client, author, detail_url, news
):
    """Тест доступа для отправки комментария авторизированного пользователя."""
    comments_count_before = Comment.objects.count()
    author_client.post(detail_url, data={'text': NEW_COMMENT_TEXT})
    comments_count_after = Comment.objects.count()
    assert comments_count_after == comments_count_before + 1
    new_cmnt = Comment.objects.get()
    assert new_cmnt.text == NEW_COMMENT_TEXT
    assert new_cmnt.news == news
    assert new_cmnt.author == author


def test_user_cant_use_bad_words(author_client, detail_url):
    """Тест на использование стоп-слов."""
    comment_count_before = Comment.objects.count()
    bad_words = {'text': f'Какой-то текст, {random.choice(BAD_WORDS)}, ...'}
    response = author_client.post(detail_url, data=bad_words)
    assertFormError(
        response,
        form='form',
        field='text',
        errors=WARNING
    )
    comment_count_after = Comment.objects.count()
    assert comment_count_after == comment_count_before


def test_auth_user_can_edit_comment(
    author_client, comment, detail_url, edit_url
):
    """Пользователь может редактировать свой комментарий."""
    response = author_client.post(
        edit_url, data={'text': NEW_COMMENT_TEXT}
    )
    assertRedirects(response, detail_url + '#comments')
    comment.refresh_from_db()
    assert comment.text == NEW_COMMENT_TEXT


def test_auth_user_can_delete_comment(
        author_client, comment, detail_url, delete_url
):
    """Пользователь может удалить свой комментарий."""
    response = author_client.delete(delete_url)
    assertRedirects(response, detail_url + '#comments')
    assert not Comment.objects.filter(id=comment.id).exists()


def test_auth_user_cant_edit_comment_of_another_user(
        author_client, comment, detail_url
):
    """Пользователь не может редактировать чужие комментарии."""
    response = author_client.post(
        detail_url, data={'text': NEW_COMMENT_TEXT}
    )
    expected_redirect_url = detail_url + '#comments'
    response = author_client.post(
        detail_url, data={'text': NEW_COMMENT_TEXT}
    )
    assertRedirects(response, expected_redirect_url)
    comment_from_db = Comment.objects.get(id=comment.id)
    assert comment.text == comment_from_db.text
    assert comment.news == comment_from_db.news
    assert comment.author == comment_from_db.author


def test_auth_user_cant_delete_comment_of_another_user(
        author_client, comment, detail_url
):
    """Пользователь не может удалять чужие комментарии."""
    comment_count_before = Comment.objects.count()
    response = author_client.delete(detail_url)
    comment_count_after = Comment.objects.count()
    assert response.status_code == HTTPStatus.METHOD_NOT_ALLOWED
    assert comment_count_after == comment_count_before
    comment.refresh_from_db()
    assert comment.text == 'Здесь написано что-то интересное!'
    assert comment.author == comment.author
