from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from notes.models import Note

User = get_user_model()


class TestRoutes(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Санта-Клаус')
        cls.notes = Note.objects.create(
            title='Заголовок',
            text='Текст',
            author=cls.author,
            slug='Example_note',
        )
        cls.not_author = User.objects.create(username='Кто-то')

    def test_pages_availability(self):
        '''
        Проверяем сраницы, доступыне для всех.
        '''
        urls = (
            ('notes:home', None),
            ('users:login', None),
            ('users:logout', None),
            ('users:signup', None),
        )
        for name, args in urls:
            with self.subTest(name=name):
                url = reverse(name, args=args)
                response = self.client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_availability_for_notes_edit_and_delete_and_detail(self):
        '''
        Проверяем страницы, доступные только автору заметки
        '''
        users_statuses = (
            (self.author, HTTPStatus.OK),
            (self.not_author, HTTPStatus.NOT_FOUND),
        )
        urls = (
            ('notes:detail', (self.notes.slug,)),
            ('notes:delete', (self.notes.slug,)),
            ('notes:edit', (self.notes.slug,))
        )
        for user, status in users_statuses:
            self.client.force_login(user)
            for user, status in users_statuses:
                self.client.force_login(user)
                for name, args in urls:
                    with self.subTest(user=user, name=name):
                        url = reverse(name, args=args)
                        response = self.client.get(url)
                        self.assertEqual(response.status_code, status)

    def test_redirect_for_anonymous_client(self):
        '''
        Проверяем редирект для неавторизованного пользователя.
        '''
        login_url = reverse('users:login')
        urls = (
            ('notes:edit', (self.notes.slug,)),
            ('notes:delete', (self.notes.slug,)),
            ('notes:list', None),
            ('notes:add', None),
            ('notes:success', None),
            ('notes:detail', (self.notes.slug,)),
        )
        for name, args in urls:
            with self.subTest(name=name):
                url = reverse(name, args=args)
                redirect_url = f'{login_url}?next={url}'
                response = self.client.get(url)
                self.assertRedirects(response, redirect_url)

    def test_page_availability_for_author(self):
        '''Проверяем доступность страниц для автора.
        '''
        urls = (
            'notes:list', 'notes:success', 'notes:add',
        )
        for name in urls:
            with self.subTest(name=name):
                url = reverse(name)
                self.client.force_login(self.author)
                response = self.client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)