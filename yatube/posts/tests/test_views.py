from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from ..forms import PostForm
from ..models import Post, Group, Follow, Comment

User = get_user_model()
LIMIT = 10
REMAINS = 6


class ViewsTests(TestCase):
    """Класс тестирования страниц."""

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
        for i in range(15):
            cls.new_post1 = Post.objects.create(
                author=cls.user,
                text=f'Текст поста {i + 1}',
                group=cls.group
            )
        cls.index_url = reverse('posts:index')
        cls.group_url = reverse(
            'posts:group_posts',
            kwargs={'slug': ViewsTests.group.slug}
        )
        cls.profile_url = reverse(
            'posts:profile',
            kwargs={'username': ViewsTests.user.username}
        )
        cls.post_detail_url = reverse(
            'posts:post_detail',
            kwargs={'post_id': ViewsTests.post.pk}
        )
        cls.pots_create_url = reverse('posts:post_create')
        cls.post_edit_url = reverse(
            'posts:post_edit',
            kwargs={'post_id': ViewsTests.post.pk}
        )
        cls.add_comment_url = reverse(
            'posts:add_comment',
            kwargs={'post_id': ViewsTests.post.pk}
        )
        cls.follow_url = reverse(
            'posts:profile_follow',
            kwargs={'username': ViewsTests.user.username}
        )
        cls.unfollow_url = reverse(
            'posts:profile_unfollow',
            kwargs={'username': ViewsTests.user.username}
        )
        cls.follow_index_url = reverse('posts:follow_index')
        cls.urls_templates = {
            ViewsTests.post_edit_url: 'posts/create_post.html',
            ViewsTests.pots_create_url: 'posts/create_post.html',
            ViewsTests.post_detail_url: 'posts/post_detail.html',
            ViewsTests.profile_url: 'posts/profile.html',
            ViewsTests.group_url: 'posts/group_list.html',
            ViewsTests.index_url: 'posts/index.html',
            ViewsTests.follow_index_url: 'posts/follow.html'
        }

    def setUp(self):
        """Метод с фикстурами."""
        # Устанавливаем данные для тестирования
        # Создаём экземпляр клиента. Он неавторизован.
        self.guest_client = Client()
        # Создаем пользователя
        self.auth_user = User.objects.create_user(username='HasNoName')
        # Создаем второй клиент
        self.authorized_client = Client()
        # Авторизуем пользователя
        self.authorized_client.force_login(self.auth_user)
        # авторизуем автора поста
        self.author = Client()
        self.author.force_login(ViewsTests.user)
        # соотношение view к шаблону

    def test_views_uses_correct_templates(self):
        for url, template in ViewsTests.urls_templates.items():
            response = self.author.get(url)
            self.assertTemplateUsed(response, template)

    def test_first_page_paginator(self):
        """Проверяем что на первой странице отображается 10 постов."""
        views = (
            ViewsTests.index_url,
            ViewsTests.group_url,
            ViewsTests.profile_url
        )
        for view in views:
            response = self.author.get(view)
            # Проверка: количество постов на первой странице равно 10.
            self.assertEqual(
                len(response.context['page_obj']),
                LIMIT,
                f'Пагинатор отображает неправильное '
                f'количество постов на странице {view}.'
            )

    def test_second_page_paginator(self):
        """Проверяем пагинатор на второй странице."""
        views = (
            ViewsTests.index_url,
            ViewsTests.group_url,
            ViewsTests.profile_url
        )
        for view in views:
            response = self.author.get(view + '?page=2')
            self.assertEqual(
                len(response.context['page_obj']),
                REMAINS,
                f'Пагинатор отображает неправильное '
                f'количество постов на второй странице {view}.'
            )

    def test_context_pages(self):
        """Проверяем контексты страниц index, group, profile."""
        views = (
            ViewsTests.index_url,
            ViewsTests.group_url,
            ViewsTests.profile_url
        )
        for view in views:
            response = self.author.get(view)
            first_object = response.context['posts'][0]
            self.assertEqual(
                first_object.text,
                'Текст поста 15',
                f'{view} отображает пост с неправильным текстом.'
            )
            self.assertEqual(
                first_object.group,
                ViewsTests.group,
                f'{view} отображает пост с неправильной группой.'
            )
            self.assertEqual(
                first_object.author,
                ViewsTests.user,
                f'{view} отображает пост с неправильным автором.'
            )

    def test_post_detail_context(self):
        """Проверка контекста страницы поста."""
        response = self.author.get(ViewsTests.post_detail_url)
        self.assertEqual(
            response.context['post'].text,
            'Тестовый пост',
            'Страница поста отображает пост с неправильным текстом.'
        )
        self.assertEqual(
            response.context['post'].author,
            ViewsTests.user,
            'Страница поста отображает неправильного автора.'
        )
        self.assertEqual(
            response.context['post'].group,
            ViewsTests.group,
            'Страница поста отображает неправильную группу.'
        )

    def test_create_post_context(self):
        """Проверка контекста страницы создания поста."""
        response = self.author.get(ViewsTests.pots_create_url)
        self.assertIsInstance(response.context.get('form'), PostForm)

    def test_edit_post_context(self):
        """Проверка контекста страницы редактирования поста."""
        response = self.author.get(ViewsTests.post_edit_url)
        self.assertIsInstance(response.context.get('form'), PostForm)
        self.assertTrue(
            response.context['is_edit'],
            'View функция передала направильный контекст is_edit'
        )

    def test_home_page_after_create_new_post(self):
        """Проверяем появился ли пост на главной странице."""
        last_post = Post.objects.create(
            author=ViewsTests.user,
            text='Это самый новый пост',
            group=ViewsTests.group
        )
        response = self.authorized_client.get(ViewsTests.index_url)
        self.assertEqual(response.context['posts'][0], last_post)

    def test_profile_page_after_create_new_post(self):
        """Проверяем появился ли пост на странице пользователя."""
        last_post = Post.objects.create(
            author=ViewsTests.user,
            text='Это самый новый пост',
            group=ViewsTests.group
        )
        response = self.authorized_client.get(ViewsTests.profile_url)
        self.assertEqual(response.context['posts'][0], last_post)

    def test_group_page_after_create_new_post(self):
        """Проверяем появился ли пост на странице группы."""
        last_post = Post.objects.create(
            author=ViewsTests.user,
            text='Это самый новый пост',
            group=ViewsTests.group
        )
        response = self.authorized_client.get(ViewsTests.group_url)
        self.assertEqual(response.context['posts'][0], last_post)

    def test_user_create_comment(self):
        """Проверяем что комментарии создаются и отобрадаются."""
        data = {'text': 'тестовый комментарий'}
        # создадим комментарий
        response = self.author.post(
            ViewsTests.add_comment_url,
            data=data,
            follow=True
        )
        # проверяем что перешли на страницу поста
        self.assertRedirects(response, f'/posts/{ViewsTests.post.pk}/')
        # проверяем что на странице поста комментарий появился
        response = self.author.get(ViewsTests.post_detail_url)
        self.assertEqual(response.context['comments'][0].text, data['text'])

    def test_guest_cant_create_comment(self):
        """Проверяем что гость не может создавать комментарии."""
        data = {'text': 'тестовый комментарий'}
        count = Comment.objects.count()
        response = self.guest_client.post(
            ViewsTests.add_comment_url,
            data=data,
            follow=True
        )
        # проверяем что количество комментириев в базе не меняется
        self.assertEqual(Comment.objects.count(), count)
        self.assertRedirects(
            response,
            f'/auth/login/?next=/posts/{ViewsTests.post.pk}/comment/'
        )

    def test_cache_on_index_page(self):
        """Проверяем кеширование главной страницы."""
        new_post = Post.objects.create(
            author=ViewsTests.user,
            text='Кешированный пост',
            group=ViewsTests.group
        )
        response = self.author.get(ViewsTests.index_url)
        page_post = response.context['posts'][0]
        self.assertEqual(page_post, new_post)
        new_post.delete()
        response = self.author.get(ViewsTests.index_url)
        new_page_post = response.context['posts'][0]
        self.assertEqual(new_page_post, page_post)

    def test_following(self):
        """Проверяем что пользователь может подписываться на авторов."""
        # подпишемся на автора
        response = self.authorized_client.get(ViewsTests.follow_url)
        self.assertTrue(
            Follow.objects.filter(
                user=self.auth_user,
                author=ViewsTests.user
            ).count()
        )
        response = self.authorized_client.get(ViewsTests.follow_index_url)
        # проверим что посты автора появились на странице ленты
        posts = response.context['posts']
        self.assertTrue(
            posts.filter(author=ViewsTests.user).count()
        )
        # проверим что постов других авторов нет
        self.assertEqual(posts.filter(author=self.auth_user).count(), 0)
        # отписались от автора
        response = self.authorized_client.get(ViewsTests.unfollow_url)
        response = self.authorized_client.get(ViewsTests.follow_index_url)
        self.assertEqual(response.context['posts'].count(), 0)
