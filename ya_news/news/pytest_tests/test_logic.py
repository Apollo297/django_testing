from http import HTTPStatus

import pytest
from django.conf import settings
from django.urls import reverse
from pytest_django.asserts import assertFormError, assertRedirects

from news.forms import BAD_WORDS, WARNING
from news.models import Comment

COMMENT_TEXT = 'Текст комментария'
DELETE_URL = 'news:delete'
EDIT_URL = 'news:edit'
COMMENT_CHANGING = 1


@pytest.mark.django_db
@pytest.mark.parametrize(
    'name, args',
    (
        (settings.DETAIL_URL, pytest.lazy_fixture('pk_for_args_news')),
    ),
)
def test_anonymous_user_cant_create_comment(

    client,
    form_data,
    name,
    args
):
    """Анонимный пользователь не может отправить комментарий."""
    db_comment_data = Comment.objects.count()
    url = reverse(name, args=args)
    response = client.post(url, data=form_data)
    login_url = reverse('users:login')
    expected_url = f'{login_url}?next={url}'
    want_to_get = Comment.objects.count()
    assertRedirects(response, expected_url)
    assert db_comment_data == want_to_get


@pytest.mark.django_db
@pytest.mark.parametrize(
    'name, args',
    (
        (settings.DETAIL_URL, pytest.lazy_fixture('pk_for_args_news')),
    ),
)
def test_user_can_create_comment(
    author_client,
    author,
    form_data,
    name,
    args,
    news
):
    """Авторизованный пользователь может отправить комментарий."""
    url = reverse(name, args=args)
    db_comment_data = Comment.objects.count()
    want_to_get = url + '#comments'
    response = author_client.post(url, data=form_data)
    assertRedirects(response, want_to_get)
    db_comment_data_after = Comment.objects.count()
    expected_number = db_comment_data_after - COMMENT_CHANGING
    assert db_comment_data == expected_number
    new_comment = Comment.objects.last()
    assert new_comment.text == form_data['text']
    assert new_comment.author == author
    assert new_comment.news == news


@pytest.mark.parametrize(
    'name, args',
    (
        (settings.DETAIL_URL, pytest.lazy_fixture('pk_for_args_news')),
    ),
)
def test_user_cant_use_bad_words(author_client, name, args):
    """
    Если комментарий содержит запрещённые слова, он не будет опубликован,
    а форма вернёт ошибку.
    """
    db_comment_data = Comment.objects.count()
    url = reverse(name, args=args)
    bad_words_data = {'text': f'Какой-то текст, {BAD_WORDS[0]}, еще текст'}
    response = author_client.post(url, data=bad_words_data)
    assertFormError(
        response,
        form='form',
        field='text',
        errors=WARNING
    )
    comments_count = Comment.objects.count()
    assert comments_count == db_comment_data


@pytest.mark.parametrize(
    'name, args',
    (
        (DELETE_URL, pytest.lazy_fixture('pk_for_args_comment')),
    ),
)
def test_author_can_delete_comment(
        author_client,
        pk_for_args_news,
        name,
        args
):
    """Авторизованный пользователь может удалять свои комментарии."""
    db_comment_data = Comment.objects.count() - COMMENT_CHANGING
    url = reverse(name, args=args)
    response = author_client.post(url)
    want_to_get = reverse(
        settings.DETAIL_URL,
        args=pk_for_args_news
    ) + '#comments'
    assertRedirects(response, want_to_get)
    comments_count = Comment.objects.count()
    assert comments_count == db_comment_data


@pytest.mark.parametrize(
    'name, args',
    (
        (DELETE_URL, pytest.lazy_fixture('pk_for_args_comment')),
    ),
)
def test_other_user_cant_delete_comment_of_another_user(
        admin_client,
        name,
        args
):
    """Авторизованный пользователь не может удалять чужие комментарии."""
    db_comment_data = Comment.objects.count()
    url = reverse(name, args=args)
    response = admin_client.post(url)
    assert response.status_code == HTTPStatus.NOT_FOUND
    comments_count = Comment.objects.count()
    assert db_comment_data == comments_count


@pytest.mark.parametrize(
    'name, args',
    (
        (EDIT_URL, pytest.lazy_fixture('pk_for_args_comment')),
    ),
)
def test_author_can_edit_comment(
    author_client,
    name,
    args,
    pk_for_args_news,
    form_data,
    comment,
    author,
    news
):
    """Авторизованный пользователь может редактировать свои комментарии."""
    url = reverse(name, args=args)
    response = author_client.post(url, form_data)
    want_to_get = reverse(
        settings.DETAIL_URL,
        args=pk_for_args_news
    ) + '#comments'
    assertRedirects(response, want_to_get)
    comment.refresh_from_db()
    assert comment.text == form_data['text']
    assert comment.author == author
    assert comment.news == news


@pytest.mark.parametrize(
    'name, args',
    (
        (EDIT_URL, pytest.lazy_fixture('pk_for_args_comment')),
    ),
)
def test_other_user_cant_edit_comment(
    admin_client,
    form_data,
    comment,
    name,
    args,
    author,
    news
):
    """Авторизованный пользователь может редактировать чужие комментарии."""
    url = reverse(name, args=args)
    response = admin_client.post(url, form_data)
    assert response.status_code == HTTPStatus.NOT_FOUND
    note_from_db = Comment.objects.get(id=comment.id)
    assert comment.text == note_from_db.text
    assert comment.author == author
    assert comment.news == news
