from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from pytils.translit import slugify

from notes.forms import WARNING
from notes.models import Note

User = get_user_model()
SUCCESS_URL = reverse('notes:success')


class TestNoteCreation(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Санта-Клаус')
        cls.url = reverse('notes:add')
        cls.auth_client = Client()
        cls.auth_client.force_login(cls.author)
        cls.form_data = {'title': 'Заголовок',
                         'text': 'Текст',
                         'slug': 'Example_note'}

    def test_anonymous_user_cant_create_note(self):
        '''Анонимный пользователь не может создать заметку.'''
        self.client.post(self.url, data=self.form_data)
        notes_count = Note.objects.count()
        self.assertEqual(notes_count, 0)

    def test_user_can_create_note(self):
        '''Аутентифицированный пользователь может создать заметку.'''
        response = self.auth_client.post(self.url, data=self.form_data)
        self.assertRedirects(response, SUCCESS_URL)
        notes_count = Note.objects.count()
        self.assertEqual(notes_count, 1)
        note = Note.objects.last()
        self.assertEqual(note.title, self.form_data['title'])
        self.assertEqual(note.text, self.form_data['text'])
        self.assertEqual(note.slug, self.form_data['slug'])
        self.assertEqual(note.author, self.author)

    def test_user_can_use_only_unique_slug(self):
        '''Проверка уникальности слага.'''
        self.client.force_login(self.author)
        self.client.post(self.url, data=self.form_data)
        response = self.client.post(self.url, data=self.form_data)
        forbidden = self.form_data['slug'] + WARNING
        self.assertFormError(
            response,
            form='form',
            field='slug',
            errors=forbidden
        )

    def test_empty_slug(self):
        '''
        Проверка возможности создания заметки с автоматической
        генерацией слага.
        '''
        self.client.force_login(self.author)
        del self.form_data['slug']
        response = self.client.post(self.url, data=self.form_data)
        self.assertRedirects(response, SUCCESS_URL)
        self.assertEqual(Note.objects.count(), 1)
        new_note = Note.objects.last()
        expected_slug = slugify(self.form_data['title'])
        self.assertEqual(new_note.slug, expected_slug)


class TestNoteEditDelete(TestCase):
    NOTE_TEXT = 'Текст заметки.'
    NEW_NOTE_TEXT = 'Новый текст заметки.'
    NOTE_TITLE = 'Название'
    NEW_TITLE_TEXT = 'Новое название'

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Автор заметки')
        cls.author_client = Client()
        cls.author_client.force_login(cls.author)
        cls.reader = User.objects.create(username='Не автор заметки')
        cls.reader_client = Client()
        cls.reader_client.force_login(cls.reader)
        cls.notes = Note.objects.create(
            title=cls.NOTE_TITLE,
            text=cls.NOTE_TEXT,
            author=cls.author,
            slug='Example_note',
        )
        cls.edit_url = reverse('notes:edit', args=(cls.notes.slug,))
        cls.delete_url = reverse('notes:delete', args=(cls.notes.slug,))
        cls.form_data = {'text': cls.NEW_NOTE_TEXT,
                         'title': cls.NEW_TITLE_TEXT}

    def test_author_can_delete_notes(self):
        '''Автор заметки может её удалить.'''
        response = self.author_client.delete(self.delete_url)
        self.assertRedirects(response, SUCCESS_URL)
        comments_count = Note.objects.count()
        self.assertEqual(comments_count, 0)

    def test_user_cant_delete_note_of_another_user(self):
        '''Пользователь не может удалить не свою заметку.'''
        response = self.reader_client.delete(self.delete_url)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        comments_count = Note.objects.count()
        self.assertEqual(comments_count, 1)

    def test_author_can_edit_note(self):
        '''Автор заметки может её редактировать.'''
        response = self.author_client.post(self.edit_url, self.form_data)
        self.assertRedirects(response, SUCCESS_URL)
        self.notes.refresh_from_db()
        self.assertEqual(self.notes.text, self.NEW_NOTE_TEXT)
        self.assertEqual(self.notes.title, self.NEW_TITLE_TEXT)
        self.assertEqual(self.notes.author, self.author)

    def test_user_cant_edit_note_of_another_user(self):
        '''Пользователь не может редактировать заметки другого пользователя.'''
        response = self.reader_client.post(self.edit_url, data=self.form_data)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.notes.refresh_from_db()
        self.assertEqual(self.notes.text, self.NOTE_TEXT)
        self.assertEqual(self.notes.title, self.NOTE_TITLE)
        self.assertEqual(self.notes.author, self.author)
