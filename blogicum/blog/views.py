from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import UpdateView, DetailView
from django.urls import reverse_lazy, reverse
from django.http import Http404
from django.utils import timezone
from .models import Category, Post, Comment
from django.core.paginator import Paginator
from .forms import PostForm, CommentForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import CommentForm
from django.db.models import Count
from django.core.exceptions import PermissionDenied
from .forms import DeleteConfirmForm

User = get_user_model()


def post_detail(request, id):
    template = 'blog/detail.html'
    post = get_object_or_404(
        Post.objects.select_related('author', 'location', 'category')
            .prefetch_related('comments__author'),
        pk=id
    )

    # Проверяем, доступен ли пост текущему пользователю
    if not (post.is_published
            and post.category.is_published
            and post.pub_date <= timezone.now()):
        # Если пост не опубликован, проверяем, является ли пользователь автором
        if request.user != post.author:
            raise Http404("Пост не найден или недоступен")

    comments = post.comments.select_related('author')
    comment_form = CommentForm()

    context = {
        'post': post,
        'comments': comments,
        'form': comment_form,
    }

    return render(request, template, context)


def category_posts(request, category_slug):
    template = 'blog/category.html'

    category = get_object_or_404(
        Category,
        slug=category_slug,
        is_published=True
    )

    page_obj = Post.objects.filter(
        category=category,
        is_published=True,
        pub_date__lte=timezone.now()
    ).annotate(
        comment_count=Count('comments')
    ).order_by('-pub_date')

    paginator = Paginator(page_obj, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'category': category,
        'page_obj': page_obj,
    }

    return render(request, template, context)


def index(request):
    template = 'blog/index.html'

    page_obj = Post.objects.filter(
        is_published=True,
        pub_date__lte=timezone.now(),
        category__is_published=True
    ).select_related('category', 'location', 'author').annotate(
        comment_count=Count('comments')
    ).order_by('-pub_date')

    paginator = Paginator(page_obj, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {'page_obj': page_obj}

    return render(request, template, context)


@login_required
def create_post(request):
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            return redirect(reverse('blog:profile',
                                    kwargs={
                                        'username': request.user.username}))
    else:
        form = PostForm()

    return render(request, 'blog/create.html', {'form': form})


@login_required(login_url='/auth/login/')
def post_edit(request, id):  # Параметр называется post_id
    post = get_object_or_404(Post, pk=id)

    if request.user != post.author:
        messages.error(request, 'Вы не можете редактировать этот пост')
        return redirect('blog:post_detail', id=post.id)  # Используем post_id

    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES, instance=post)
        if form.is_valid():
            edited_post = form.save()
            messages.success(request, 'Пост успешно обновлён')
            return redirect('blog:post_detail', id=edited_post.id)
    else:
        form = PostForm(instance=post)

    return render(request, 'blog/create.html', {'form': form})


class ProfileView(DetailView):
    model = User
    template_name = 'blog/profile.html'
    context_object_name = 'profile'
    slug_field = 'username'
    slug_url_kwarg = 'username'
    paginate_by = 10

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.object
        posts = Post.objects.filter(author=user).annotate(
            comment_count=Count('comments')
        ).order_by('-pub_date')

        paginator = Paginator(posts, self.paginate_by)
        page_number = self.request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        context['page_obj'] = page_obj
        return context


class ProfileEditView(LoginRequiredMixin, UpdateView):
    model = User
    fields = ['first_name', 'last_name', 'email']
    template_name = 'blog/user.html'

    def get_object(self, queryset=None):
        # Return the current user
        return self.request.user

    def get_success_url(self):
        return reverse_lazy('blog:profile',
                            kwargs={'username': self.request.user.username})


def delete_post(request, pk):
    post = get_object_or_404(Post, pk=pk)

    # Check if the user is the author of the post
    if request.user != post.author:
        messages.error(request, 'Вы не можете удалить этот пост')
        return redirect('blog:post_detail', id=pk)

    if request.method == 'POST':
        post.delete()
        messages.success(request, 'Пост успешно удалён')
        return redirect('blog:profile', username=request.user.username)

    # For GET request, show confirmation page
    form = DeleteConfirmForm()
    return render(request, 'blog/create.html', {
        'form': form,
        'post': post,  # Pass the post to the template
    })


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.author = request.user
            comment.post = post
            comment.save()
    return redirect('blog:post_detail', id=post_id)


@login_required
def edit_comment(request, post_id, comment_id):
    comment = get_object_or_404(Comment, pk=comment_id)
    if comment.author != request.user:
        return redirect('blog:post_detail', id=post_id)
    if request.method == 'POST':
        form = CommentForm(request.POST, instance=comment)
        if form.is_valid():
            form.save()
            return redirect('blog:post_detail', id=post_id)
    else:
        form = CommentForm(instance=comment)
    return render(
        request,
        'blog/comment.html',
        {'form': form, 'comment': comment}
    )


@login_required
def delete_comment(request, post_id, comment_id):
    post = get_object_or_404(Post, pk=post_id)
    comment = get_object_or_404(Comment, pk=comment_id)

    if request.method == 'POST':
        if comment.author != request.user and not request.user.is_staff:
            raise PermissionDenied
        comment.delete()
        return redirect('blog:post_detail', id=post_id)

    return render(request, 'blog/comment.html', {
        'post': post,
        'comment': comment
    })
