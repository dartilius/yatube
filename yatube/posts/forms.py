from django import forms

from posts.models import Post, Comment


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ('text', 'group', 'image')

    def clean_text(self):
        data = self.cleaned_data['text']

        if not data:
            raise forms.ValidationError('Заполните поле text')

        return data


class CommentForm(forms.ModelForm):
    """Форма создания комментария."""
    class Meta:
        model = Comment
        fields = ('text',)

    def clean_text(self):
        data = self.cleaned_data['text']

        if not data:
            raise forms.ValidationError('Заполните поле text')

        return data
