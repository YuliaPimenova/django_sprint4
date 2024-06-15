from datetime import datetime
import pytz

from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import (
    CreateView, DeleteView, DetailView, ListView, UpdateView)
from django.urls import reverse

from .forms import CommentForm, PostForm, UserUpdateForm
from .mixins import CommentMixin, OnlyAuthorMixin, PostMixin
from .models import Category, Post

PAGINATE_COUNT = 10

User = get_user_model()


def post_filter(query):
    return query.select_related('category').filter(
        pub_date__lte=datetime.now(),
        is_published__exact=True,
        category__is_published=True
    ).order_by('-pub_date')


class PostListView(ListView):
    model = Post
    paginate_by = PAGINATE_COUNT
    template_name = 'blog/index.html'

    def get_queryset(self):
        return post_filter(super().get_queryset().annotate(
            comment_count=Count('comments')
        ))


class PostCreateView(LoginRequiredMixin, PostMixin, CreateView):

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)


class PostUpdateView(PostMixin, UpdateView):

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        if self.request.user != self.object.author:
            return redirect(reverse('blog:post_detail', args=[self.object.pk]))
        return super().dispatch(request, *args, **kwargs)


class PostDeleteView(OnlyAuthorMixin, PostMixin, DeleteView):

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = PostForm(instance=self.object)
        return context


class PostDetailView(DetailView):
    model = Post
    template_name = 'blog/detail.html'

    def get_object(self, queryset=None):
        object = super().get_object(queryset=queryset)
        if self.request.user != object.author and (
            object.pub_date > datetime.now().replace(
                tzinfo=pytz.utc) or not object.is_published):
            raise Http404
        return object

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = CommentForm()
        context['comments'] = (
            self.get_object().comments.select_related('author')
        )
        return context


class CategoryListView(ListView):
    model = Category
    template_name = 'blog/category.html'
    paginate_by = PAGINATE_COUNT

    def dispatch(self, request, *args, **kwargs):
        self.category = get_object_or_404(
            Category,
            slug__exact=self.kwargs['category_slug'],
            is_published__exact=True
        )
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return post_filter(self.category.posts.all()).annotate(
            comment_count=Count('comments')
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category'] = self.category
        return context


class ProfileListView(ListView):
    model = User
    template_name = 'blog/profile.html'
    paginate_by = PAGINATE_COUNT

    def dispatch(self, request, *args, **kwargs):
        self.profile = get_object_or_404(User, username=kwargs['username'])
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        if self.request.user == self.profile:
            return self.profile.posts.all().annotate(
                comment_count=Count('comments')
            ).order_by('-pub_date')
        return post_filter(self.profile.posts.all()).annotate(
            comment_count=Count('comments'))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['profile'] = self.profile
        return context


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    model = User
    form_class = UserUpdateForm
    template_name = 'blog/user.html'

    def get_object(self, queryset=None):
        return self.request.user

    def get_success_url(self):
        return reverse('blog:profile',
                       kwargs={'username': self.request.user.username})


class CommentCreateView(LoginRequiredMixin, CommentMixin, CreateView):

    def form_valid(self, form):
        form.instance.author = self.request.user
        form.instance.post = self.post_card
        return super().form_valid(form)


class CommentUpdateView(OnlyAuthorMixin, CommentMixin, UpdateView):
    template_name = 'blog/comment.html'


class CommentDeleteView(OnlyAuthorMixin, CommentMixin, DeleteView):
    template_name = 'blog/comment.html'
