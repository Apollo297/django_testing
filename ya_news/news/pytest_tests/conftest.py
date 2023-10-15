from datetime import datetime, timedelta

import pytest
from django.conf import settings
from django.utils import timezone

from news.models import Comment, News

COMMENT_TEXT = 'Текст комментария'


@pytest.fixture
def author(django_user_model):
    return django_user_model.objects.create(username='Автор')


@pytest.fixture
def author_client(author, client):
    client.force_login(author)
    return client


@pytest.fixture
def news():
    news = News.objects.create(
        title='Заголовок',
        text='Текст',
    )
    return news


@pytest.fixture
def comment(news, author):
    comment = Comment.objects.create(
        news=news,
        text='Какой-то текст',
        author=author,
    )
    return comment


@pytest.fixture
def pk_for_args_news(news):
    return news.pk,


@pytest.fixture
def pk_for_args_comment(comment):
    return comment.pk,


@pytest.fixture
def news_list():
    today = datetime.today()
    all_news = []
    for index in range(settings.NEWS_COUNT_ON_HOME_PAGE + 1):
        news = News(
            title=f'Новость {index}',
            text='Просто текст.',
            date=today - timedelta(days=index)
        )
        all_news.append(news)
        News.objects.bulk_create(all_news)


@pytest.fixture
def comments_list(news, author):
    now = timezone.now()
    for index in range(2):
        comment = Comment.objects.create(
            news=news,
            author=author,
            text=f'Tекст {index}',
        )
        comment.created = now + timedelta(days=index)
        comment.save()


@pytest.fixture
def form_data():
    return {
        'text': COMMENT_TEXT,
    }
