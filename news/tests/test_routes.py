"""
Тесты доступности конкретных эндпоинтов.

Проверка редиректов, кодов ответа,
которые возвращают страницы, тестирование доступа
для авторизованных или анонимных пользователей.
"""

# news/tests/test_routes.py
# Импортируем класс HTTPStatus.
from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import TestCase
# Импортируем функцию reverse().
from django.urls import reverse

# Импортируем News
from news.models import Comment, News

User = get_user_model()

class TestRoutes(TestCase):

    # Добавляем фикстуру с созданием первой новости
    @classmethod
    def setUpTestData(cls):
        cls.news = News.objects.create(
            title='Заголовок',
            text='Текст'
        )
        # Создаем двух пользователей с разными именами
        cls.author = User.objects.create(username='Лев Толстой')
        cls.reader = User.objects.create(username='Читатель простой')
        # От имени одного пользователя создаем комментарий к новости
        cls.comment = Comment.objects.create(
            news=cls.news,
            author=cls.author,
            text='Текст комментария'
        )

    def test_pages_availability(self):
        # Создаем набор тестовых данных - кортеж кортежей.
        # Каждый вложенный кортеж содержит два элемента:
        # имя пути и позиционные аргументы для функции reverse().
        urls = (
            ('news:home', None),
            ('news:detail', (self.news.id,)),
            ('users:login', None),
            ('users:logout', None),
            ('users:signup', None),
        )
        # Итерируемся по внешнему кортежу
        # и распаковываем содержимое вложенных кортежей:
        for name, args in urls:
            with self.subTest(name=name):
                # Передаем имя и позиционный аргумент в reverse()
                # и получаем адрес страницы для GET-запроса:
                url = reverse(name, args=args)
                response = self.client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

        def test_availability_for_comment_edit_and_delete(self):
            # При обращении к страницам редактирования и удаления комментария
            users_statuses = (
                # Автор комментария должен получить ответ ОК
                (self.author, HTTPStatus.OK),
                # Читатель должен получить ответ NOT_FOUND
                (self.reader, HTTPStatus.NOT_FOUND),
            )
            for user, status in users_statuses:
                # Логиним пользователя в клиенте:
                self.client.force_login(user)
                # Для каждой пары "пользователь - ожидаемый ответ"
                # Перебираем имена тестируемых страниц
                for name in ('news:edit', 'news:delete'):
                    with self.subTest(user=user, name=name):
                        url = reverse(name, args=(self.comment.id,))
                        response = self.client.get(url)
                        self.assertEqual(response.status_code, status)

        def test_redirect_for_anonymous_client(self):
            # Сохраняем адрес страницы логина
            login_url = reverse('users:login')
            # В цикле перебираем имена страниц, с которых ожидаем редирект
            for name in ('news:edit', 'news:delete'):
                with self.subTest(name=name):
                    # Получаем адрес страницы редактирования 
                    # или удаления комментария
                    url = reverse(name, args=(self.comment.id,))
                    # Получаем ожидаемый адрес страницы логина,
                    # на который будет перенаправлен пользователь.
                    # Учитываем, что в адресе будет параметр next,
                    # в котором передается адрес страницы,
                    # с которой пользователь был переадресован.
                    redirect_url = f'{login_url}?next={url}'
                    response = self.client.get(url)
                    # Проверяем, что редирект приведет
                    # именно на указанную ссылку
                    self.assertRedirects(response, redirect_url)
