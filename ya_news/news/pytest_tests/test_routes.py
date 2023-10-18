from http import HTTPStatus

import pytest
from django.urls import reverse
from pytest_django.asserts import assertRedirects


@pytest.mark.django_db
@pytest.mark.parametrize(
    'name, args',
    (
        ('news:home', None),
        ('users:login', None),
        ('users:logout', None),
        ('users:signup', None),
        ('news:detail', pytest.lazy_fixture('pk_for_args_news')),
    ),
)
def test_pages_availability_for_anonymous_user(client, name, args):
    """Страницы, доступные анонимному пользователю."""
    url = reverse(name, args=args)
    response = client.get(url)
    assert response.status_code == HTTPStatus.OK


@pytest.mark.parametrize(
    'name, args',
    (
        ('news:edit', pytest.lazy_fixture('pk_for_args_comment')),
        ('news:delete', pytest.lazy_fixture('pk_for_args_comment')),
    ),
)
def test_availability_for_author_edit_and_delete_comment(
    author_client,
    name,
    args
):
    """
    Страницы удаления и редактирования комментария доступны автору
    комментария.
    """
    url = reverse(name, args=args)
    response = author_client.get(url)
    assert response.status_code == HTTPStatus.OK


@pytest.mark.django_db
@pytest.mark.parametrize(
    'name, args',
    (
        ('news:edit', pytest.lazy_fixture('pk_for_args_comment')),
        ('news:delete', pytest.lazy_fixture('pk_for_args_comment')),
    ),
)
def test_redirect_for_anonymous_client(client, name, args):
    """
    При попытке перейти на страницу редактирования или удаления
    комментария анонимный пользователь перенаправляется на
    страницу авторизации.
    """
    login_url = reverse('users:login')
    url = reverse(name, args=args)
    expected_url = f'{login_url}?next={url}'
    response = client.get(url)
    assertRedirects(response, expected_url)


@pytest.mark.parametrize('name', ('news:edit', 'news:delete'))
def test_availability_for_other_users(
        name,
        admin_client,
        pk_for_args_comment
):
    """
    Авторизованный пользователь не может зайти на страницы
    редактирования или удаления чужих комментариев
    (возвращается ошибка 404).
    """
    url = reverse(name, args=pk_for_args_comment)
    response = admin_client.get(url)
    assert response.status_code == HTTPStatus.NOT_FOUND
