from http import HTTPStatus

import pytest
from django.urls import reverse
from pytest_django.asserts import assertFormError, assertRedirects

from news.forms import BAD_WORDS, WARNING
from news.models import Comment

COMMENT_TEXT = 'Текст комментария'


@pytest.mark.django_db
def test_anonymous_user_cant_create_comment(

    client,
    pk_for_args_news,
    form_data
):
    '''
    Анонимный пользователь не может отправить комментарий.
    '''
    url = reverse('news:detail', args=pk_for_args_news)
    response = client.post(url, data=form_data)
    login_url = reverse('users:login')
    expected_url = f'{login_url}?next={url}'
    assertRedirects(response, expected_url)
    assert Comment.objects.count() == 0


@pytest.mark.django_db
def test_user_can_create_comment(
    author_client,
    pk_for_args_news,
    author,
    form_data
):
    '''
    Авторизованный пользователь может отправить комментарий.
    '''
    url = reverse('news:detail', args=pk_for_args_news)
    want_to_get = url + '#comments'
    response = author_client.post(url, data=form_data)
    assertRedirects(response, want_to_get)
    assert Comment.objects.count() == 1
    new_comment = Comment.objects.get()
    assert new_comment.text == form_data['text']
    assert new_comment.author == author


def test_user_cant_use_bad_words(author_client, pk_for_args_news):
    '''
    Если комментарий содержит запрещённые слова, он не будет опубликован,
    а форма вернёт ошибку.
    '''
    url = reverse('news:detail', args=pk_for_args_news)
    bad_words_data = {'text': f'Какой-то текст, {BAD_WORDS[0]}, еще текст'}
    response = author_client.post(url, data=bad_words_data)
    assertFormError(
        response,
        form='form',
        field='text',
        errors=WARNING
    )
    comments_count = Comment.objects.count()
    assert comments_count == 0


def test_author_can_delete_comment(
        author_client,
        pk_for_args_news,
        pk_for_args_comment
):
    '''
    Авторизованный пользователь может удалять свои комментарии.
    '''
    url = reverse('news:delete', args=pk_for_args_comment)
    response = author_client.post(url)
    want_to_get = reverse(
        'news:detail',
        args=pk_for_args_news
    ) + '#comments'
    assertRedirects(response, want_to_get)
    assert Comment.objects.count() == 0


def test_other_user_cant_delete_comment_of_another_user(
        admin_client,
        pk_for_args_comment,
):
    '''
    Авторизованный пользователь не может удалять чужие комментарии.
    '''
    url = reverse('news:delete', args=pk_for_args_comment)
    response = admin_client.post(url)
    assert response.status_code == HTTPStatus.NOT_FOUND
    assert Comment.objects.count() == 1


def test_author_can_edit_comment(
    author_client,
    pk_for_args_comment,
    pk_for_args_news,
    form_data,
    comment
):
    '''
    Авторизованный пользователь может редактировать свои комментарии.
    '''
    url = reverse('news:edit', args=pk_for_args_comment)
    response = author_client.post(url, form_data)
    want_to_get = reverse(
        'news:detail',
        args=pk_for_args_news
    ) + '#comments'
    assertRedirects(response, want_to_get)
    comment.refresh_from_db()
    assert comment.text == form_data['text']


def test_other_user_cant_edit_comment(
    admin_client,
    pk_for_args_comment,
    form_data,
    comment
):
    '''
    Авторизованный пользователь может редактировать чужие комментарии.
    '''
    url = reverse('news:edit', args=pk_for_args_comment)
    response = admin_client.post(url, form_data)
    assert response.status_code == HTTPStatus.NOT_FOUND
    note_from_db = Comment.objects.get(id=comment.id)
    assert comment.text == note_from_db.text
