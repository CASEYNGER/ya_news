from django.conf import settings

from news.forms import CommentForm

FORM = 'form'
NEWS = 'news'


def test_count_news_on_home_page(client, news_list, home_url):
    """Тест на количество новостей на главной странице."""
    response = client.get(home_url)
    object_list = response.context['object_list']
    news_count = object_list.count()
    assert news_count == settings.NEWS_COUNT_ON_HOME_PAGE


def test_sorted_news(client, news_list, home_url):
    """Тест на правильную сортировку новостей (от новых к старым)."""
    response = client.get(home_url)
    object_list = response.context['object_list']
    all_dates = [news.date for news in object_list]
    sorted_dates = sorted(all_dates, reverse=True)
    assert all_dates == sorted_dates


def test_comments_order(client, news, comment_list, detail_url):
    """Тест на правильную сортировку комментариев (от новых к старым)."""
    response = client.get(detail_url)
    assert 'news' in response.context
    news = response.context['news']
    all_comments = news.comment_set.all()
    all_timestamps = [comment.created for comment in all_comments]
    sorted_timestamps = sorted(all_timestamps)
    assert all_timestamps == sorted_timestamps


def test_anonymous_client_has_no_form(client, detail_url):
    """Аноним не имеет формы."""
    response = client.get(detail_url)
    assert FORM not in response.context


def test_authorized_client_has_form(author_client, detail_url):
    """Авторизованный клиент имеет форму."""
    response = author_client.get(detail_url)
    assert FORM in response.context
    assert isinstance(response.context[FORM], CommentForm)
