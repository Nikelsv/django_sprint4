from django import forms
from .models import Post, Category, Location, Comment


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['title', 'text', 'pub_date', 'location', 'category', 'image']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ограничиваем выбор только опубликованными категориями и локациями
        self.fields['category'].queryset = Category.objects.filter(
            is_published=True
        )
        self.fields['location'].queryset = Location.objects.filter(
            is_published=True
        )
        # Делаем поле изображения необязательным для редактирования
        self.fields['image'].required = False

    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.cleaned_data.get('image') is False and hasattr(
            instance, 'image'
        ):
            instance.image.delete()
        if commit:
            instance.save()
        return instance


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('text',)
        widgets = {
            'text': forms.Textarea(attrs={'rows': 5})
        }


class DeleteConfirmForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = []  # Никаких полей не нужно, только подтверждение
