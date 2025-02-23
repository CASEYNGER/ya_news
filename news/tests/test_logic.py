"""
Тестирование бизнес-логики приложения.

Как обрабатываются те или иные формы,
разрешено ли создание объектов с неуникальными полями,
как работает специфичная логика конкретного приложения.
"""
from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

# Импортируем из файла с формами список стоп-слов и предупреждение формы.
from news.forms import BAD_WORDS, WARNING
from news.models import Comment, News

User = get_user_model()


class TestCommentCreation(TestCase):
    # Текст комментария понадобится в нескольких местах кода,
    # поэтому запишем его в атрибуты класса
    COMMENT_TEXT = 'Текст комментария'

    @classmethod
    def setUpTestData(cls):
        cls.news = News.objects.create(
            title='Заголовок',
            text='Текст'
        )
        # Адрес страницы с новостью
        cls.url = reverse('news:detail', args=(cls.news.id,))
        # Создаем пользователя и клиент, логинимся в клиенте
        cls.user = User.objects.create(username='Мимо Крокодил')
        cls.auth_client = Client()
        cls.auth_client.force_login(cls.user)
        # Данные для POST-запроса при создании комментария
        cls.form_data = {'text': cls.COMMENT_TEXT}

    def test_anonymous_user_cant_create_comment(self):
        """Анонимный пользователь не может комментировать"""
        # Совершаем запрос от анонимного клиента, в POST-запросе
        # отправляем предварительно подготовленные данные формы
        # с текстом комментария
        self.client.post(self.url, data=self.form_data)
        # Считаем количество комментариев
        comments_count = Comment.objects.count()
        # Ожидаем, что комментариев в базе нет - сравниваем с нулем
        self.assertEqual(comments_count, 0)
    
    def test_user_can_create_comment(self):
        """Залогиненный пользователь может комментировать"""
        # Совершаем запрос через авторизованный клиент
        response = self.auth_client.post(self.url, data=self.form_data)
        # Проверяем, что редирект привел к разделу с комментами
        self.assertRedirects(response, f'{self.url}#comments')
        # Считаем количество комментариев
        comments_count = Comment.objects.count()
        # Убеждаемся, что есть один комментарий
        self.assertEqual(comments_count, 1)
        # Получаем объект комментария из базы
        comment = Comment.objects.get()
        # Проверяем, что все атрибуты комментария совпадают с ожидаемыми
        self.assertEqual(comment.text, self.COMMENT_TEXT)
        self.assertEqual(comment.news, self.news)
        self.assertEqual(comment.author, self.user)
    
    def test_user_cant_use_bad_words(self):
        # Формируем данные для отправки формы;
        # первое слово из списка стоп-слов
        bad_words_data = {
            'text': f'Какой-то текст, {BAD_WORDS[0]}, еще текст'
        }
        # Отправляем запрос через авторизованный клиент
        response = self.auth_client.post(self.url, data=bad_words_data)
        # Проверяем, есть ли в ответе ошибка формы
        self.assertFormError(
            response,
            form='form',
            field='text',
            errors=WARNING
        )
        # Дополнительно убедимся, что комментарий не был создан
        comments_count = Comment.objects.count()
        self.assertEqual(comments_count, 0)


class TestCommentEditDelete(TestCase):
    # Тексты для комментариев не нужно дополнительно создавать
    # (в отличие от объектов в БД), им не нужны ссылки на self или cls,
    # поэтому их можно перечислить просто в атрибутах класса
    COMMENT_TEXT = 'Текст комментария'
    NEW_COMMENT_TEXT = 'Обновленный комментарий'

    @classmethod
    def setUpTestData(cls):
        # Создаем новость в БД
        cls.news = News.objects.create(
            title='Заголовок',
            text='Текст'
        )
        # Формируем адрес блока с комментариями, который понадобится для тестов
        # Адрес новости:
        news_url = reverse('news:detail', args=(cls.news.id,))
        # Адрес блока с комментариями
        cls.url_to_comments = news_url + '#comments'
        # Создаем пользователя - автора комментария
        cls.author = User.objects.create(username='Автор комментария')
        # Создаем клиент для пользователя-автора
        cls.author_client = Client()
        # Логиним пользователя в клиенте
        cls.author_client.force_login(cls.author)
        # Делаем все то же самое для пользователя-читателя
        cls.reader = User.objects.create(username='Читатель')
        cls.reader_client = Client()
        cls.reader_client.force_login(cls.reader)
        # Создаем объект комментария
        cls.comment = Comment.objects.create(
            news=cls.news,
            author=cls.author,
            text=cls.COMMENT_TEXT
        )
        # URL для редактирования комментария
        cls.edit_url = reverse('news:edit', args=(cls.comment.id,))
        # URL для удаления комментария
        cls.delete_url = reverse('news:delete', args=(cls.comment.id,))
        # Формируем данные для POST-запроса по обновению комментария
        cls.form_data = {'text': cls.NEW_COMMENT_TEXT}

    def test_author_can_delete_comment(self):
        """Проверка, что автор может удалить свой комментарий."""
        # От имени автора комментария отправляем DELETE-запрос на удаление
        response = self.author_client.delete(self.delete_url)
        # Проверяем, что редирект привел к разделу с комментариями
        # Заодно проверим статус-коды ответов
        self.assertRedirects(response, self.url_to_comments)
        # Считаем количество комментариев в системе
        comments_count = Comment.objects.count()
        # Ожидаем ноль комментариев в системе
        self.assertEqual(comments_count, 0)

    def test_user_cant_delete_comment_of_another_user(self):
        """Проверка, что пользователь не может удалить чужой комментарий."""
        # Выполняем запрос на удаление от пользователя-читателя
        response = self.reader_client.delete(self.delete_url)
        # Проверяем, что вернулась ошибка 404
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        # Убедимся, что комментарий по прежнему на месте
        comments_count = Comment.objects.count()
        self.assertEqual(comments_count, 1)

    def test_author_can_edit_comment(self):
        """Проверка, что только автор имеет доступ на эдит."""
        # Выполняем запрос на редактирование от имени автора комментария
        response = self.author_client.post(
            self.edit_url, data=self.form_data
        )
        # Проверим, что сработал редирект
        self.assertRedirects(response, self.url_to_comments)
        # Обновляем объект комментария
        self.comment.refresh_from_db()
        # Проверяем, что текст комментария соответствует обновленному
        self.assertEqual(self.comment.text, self.NEW_COMMENT_TEXT)

    def test_user_cant_edit_comment_of_another_user(self):
        # Выполняем запрос на редактирование
        # от имени другого пользователя
        response = self.reader_client.post(
            self.edit_url, data=self.form_data
        )
        # Проверяем, что вернулась ошибка 404
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        # Обновляем объект комментария
        self.comment.refresh_from_db()
        # Проверяем, что текст остался тем же, что и был
        self.assertEqual(self.comment.text, self.COMMENT_TEXT)