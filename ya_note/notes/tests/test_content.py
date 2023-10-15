from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from notes.models import Note

User = get_user_model()
NOTES_COUNT_ON_LIST_PAGE = 10


class TestListPage(TestCase):
    HOME_URL = reverse('notes:list')

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

    def test_authorized_client_has_form(self):
        """
        Проверяем, что пользователю передаётся форма.
        У неавторизованного пользоват. форма не отображается
        """
        urls = (
            ('notes:add', None),
            ('notes:edit', (self.notes.slug,)),
        )
        for name, args in urls:
            with self.subTest(name=name):
                self.client.force_login(self.author)
                url = reverse(name, args=args)
                response = self.client.get(url)
                self.assertIn('form', response.context)

    def test_notes_list_for_different_users(self):
        """
        Отдельная заметка передаётся на страницу со списком заметок в списке
        object_list в словаре context;
        Списки заметок пользователей не перемешиваются между собой.
        """
        users_notes = (
            (self.author, True),
            (self.not_author, False),
        )
        url = reverse('notes:list')
        for user, value in users_notes:
            self.client.force_login(user)
            with self.subTest(user=user, value=value):
                response = self.client.get(url)
                note_in_object_list = self.notes in response.context[
                    'object_list']
                self.assertEqual(note_in_object_list, value)
