import pytest
from django.conf import settings
from django.urls import reverse

from news.forms import CommentForm


HOME_URL = 'news:home'


@pytest.mark.django_db
@pytest.mark.usefixtures('news_list')
def test_news_count(author_client):
    '''Количество новостей на главной странице — не более 10.'''
    url = reverse(HOME_URL)
    response = author_client.get(url)
    news_on_page = response.context['object_list']
    news_count = len(news_on_page)
    assert news_count == settings.NEWS_COUNT_ON_HOME_PAGE


@pytest.mark.django_db
@pytest.mark.usefixtures('news_list')
def test_news_order(author_client):
    '''
    Новости отсортированы от самой свежей к самой старой.
    Свежие новости в начале списка.
    '''
    url = reverse(HOME_URL)
    response = author_client.get(url)
    news_on_page = response.context['object_list']
    all_dates = [news.date for news in news_on_page]
    sorted_dates = sorted(all_dates, reverse=True)
    assert all_dates == sorted_dates


@pytest.mark.django_db
@pytest.mark.usefixtures('comments_list')
@pytest.mark.parametrize(
    'name, args',
    (
        (settings.DETAIL_URL, pytest.lazy_fixture('pk_for_args_news')),
    ),
)
def test_comments_order(
    news,
    author_client,
    name,
    args
):
    '''
    Комментарии на странице отдельной новости отсортированы в
    хронологическом порядке: старые в начале списка, новые — в конце.
    '''
    url = reverse(name, args=args)
    response = author_client.get(url)
    assert 'news' in response.context
    news = response.context['news'].comment_set.all()
    sorted_news_comments = sorted(
        news,
        key=lambda comment: comment.created)
    for first_param, second_param in zip(news, sorted_news_comments):
        assert first_param.created == second_param.created


@pytest.mark.django_db
@pytest.mark.parametrize(
    'user, form_allowed', (
        (pytest.lazy_fixture('author_client'), True),
        (pytest.lazy_fixture('client'), False))
)
@pytest.mark.parametrize(
    'name, args',
    (
        (settings.DETAIL_URL, pytest.lazy_fixture('pk_for_args_news')),
    ),
)
def test_comment_form_contains_authorized_and_anonymous(
    user,
    form_allowed,
    name,
    args
):
    '''
    Проверка доступа к форме для отправки комментария для анонимного
    и авторизованного пользователей на странице отдельной новости.
    '''
    url = reverse(name, args=args)
    response = user.get(url)
    result = 'form' in response.context
    assert result == form_allowed
    if 'form' in response.context:
        assert isinstance(response.context['form'], CommentForm)
