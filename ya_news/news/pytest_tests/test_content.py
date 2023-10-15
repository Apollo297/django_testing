import pytest
from django.conf import settings
from django.urls import reverse

HOME_URL = 'news:home'


@pytest.mark.django_db
@pytest.mark.usefixtures('news_list')
def test_news_count(author_client):
    '''
    Количество новостей на главной странице — не более 10.
    '''
    url = reverse(HOME_URL)
    response = author_client.get(url)
    object_list = response.context['object_list']
    news_count = len(object_list)
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
    object_list = response.context['object_list']
    all_dates = [news.date for news in object_list]
    sorted_dates = sorted(all_dates, reverse=True)
    assert all_dates == sorted_dates


@pytest.mark.django_db
@pytest.mark.usefixtures('comments_list')
def test_comments_order(news, pk_for_args_news, author_client):
    '''
    Комментарии на странице отдельной новости отсортированы в
    хронологическом порядке: старые в начале списка, новые — в конце.
    '''
    detail_url = reverse('news:detail', args=pk_for_args_news)
    response = author_client.get(detail_url)
    assert 'news' in response.context
    news = response.context['news']
    all_comments = news.comment_set.all()
    assert all_comments[0].created < all_comments[1].created


@pytest.mark.django_db
@pytest.mark.usefixtures('comments_list')
def test_anonymous_client_has_no_form(client, pk_for_args_news):
    '''
    Анонимному пользователю недоступна форма для отправки комментария
    на странице отдельной новости.
    '''
    detail_url = reverse('news:detail', args=pk_for_args_news)
    response = client.get(detail_url)
    assert 'form' not in response.context


@pytest.mark.django_db
@pytest.mark.usefixtures('comments_list')
def test_authorized_client_has_form(author_client, pk_for_args_news):
    '''
    Авторизованному пользователю доступна форма для отправки комментария
    на странице отдельной новости.
    '''
    detail_url = reverse('news:detail', args=pk_for_args_news)
    response = author_client.get(detail_url)
    assert 'form' in response.context
