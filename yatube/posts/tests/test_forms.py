import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Post, Group

User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class FormsTests(TestCase):
    """Класс тестирования форм."""

    @classmethod
    def setUpClass(cls):
        """Метод с фикстурами."""
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=cls.group
        )

    def setUp(self):
        """Метод с фикстурами."""
        self.guest_client = Client()
        self.author = Client()
        # Авторизуем пользователя
        self.author.force_login(FormsTests.user)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_create_form(self):
        """Проверяем что записи создаются корректно."""
        count = Post.objects.count()
        form_data = {
            'text': 'Мы сделали новую запись!',
            'group': FormsTests.group.pk
        }
        response = self.author.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertEqual(Post.objects.count(), count + 1)
        self.assertRedirects(
            response,
            reverse(
                'posts:profile',
                kwargs={'username': FormsTests.user.username}
            )
        )
        self.assertTrue(
            Post.objects.filter(
                text=form_data['text'],
                author=FormsTests.user,
                group=form_data['group']
            ).count()
        )

    def test_edit_form(self):
        """Проверяем что запись в базе данных изменилась."""
        form_data = {
            'text': 'Мы изменили новую запись!',
            'group': FormsTests.group.pk
        }
        count = Post.objects.count()
        response = self.author.post(
            reverse(
                'posts:post_edit',
                kwargs={'post_id': FormsTests.post.pk}
            ),
            data=form_data,
            follow=True
        )
        # проверяем что новой записи не создалось
        self.assertEqual(Post.objects.count(), count)
        # проверяем что запись изменилась
        self.assertTrue(
            Post.objects.filter(
                text=form_data['text'],
                author=FormsTests.user,
                group=form_data['group']
            ).count()
        )
        # проверяем что сработал редирект
        self.assertRedirects(
            response,
            reverse(
                'posts:post_detail',
                kwargs={'post_id': FormsTests.post.pk}
            )
        )

    def test_post_with_image(self):
        """Проверяем что запись с картинкой создалась."""
        count = Post.objects.count()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        form_data = {
            'text': 'Мы сделали запись с картинкой!',
            'group': FormsTests.group.pk,
            'image': uploaded
        }
        response = self.author.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertEqual(Post.objects.count(), count + 1)
        self.assertTrue(
            Post.objects.filter(
                text=form_data['text'],
                author=FormsTests.user,
                group=form_data['group'],
                image='posts/small.gif'
            ).count()
        )
        self.assertTrue(response.status_code, 201)
