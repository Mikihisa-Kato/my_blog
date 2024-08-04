from django.db.models.query import QuerySet
from django.http import HttpResponse
from django.shortcuts import render
from django.views import generic
from .forms import ContactForm, BlogCreateForm
import logging
from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from .models import Post
from django.shortcuts import get_object_or_404

# Create your views here.
logger = logging.getLogger(__name__)

class OnlyYouMixin(UserPassesTestMixin):
    raise_exception = True
    
    def test_func(self):
        blog = get_object_or_404(Post, pk = self.kwargs['pk'])
        return self.request.user == blog.user

class IndexView(generic.TemplateView):
    template_name = 'index.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # 最新の投稿
        latest_post = Post.objects.order_by('-created_at').first()
        context['latest_post'] = latest_post
        
        # 過去の投稿を4件取得（最新の投稿を除く）
        older_posts = Post.objects.exclude(id=latest_post.id).order_by('-created_at')[:4]
        context['older_posts'] = older_posts
        
        return context
 
class ContactView(generic.FormView):
    template_name = 'contact.html'
    form_class = ContactForm
    success_url = reverse_lazy('blog:contact')
    
    def form_valid(self, form):
        form.send_email()
        messages.success(self.request, 'メッセージを送信しました。')
        logger.info('Contact sent by {}'.format(form.cleaned_data['name']))
        return super().form_valid(form)    
    
class BlogListView(LoginRequiredMixin, generic.ListView):
    model = Post
    template_name = 'blog_list.html'
    context_object_name = 'blog_list'
    paginate_by = 3
    
    def get_queryset(self):
        blogs = Post.objects.filter(user = self.request.user).order_by('-created_at')
        return blogs
    
class BlogDetailView(LoginRequiredMixin, OnlyYouMixin, generic.DetailView):
    model = Post
    template_name = 'blog_detail.html'

class BlogCreateView(LoginRequiredMixin, generic.CreateView):
    model = Post
    template_name = 'blog_create.html'
    form_class = BlogCreateForm
    success_url = reverse_lazy('blog:blog_list')
    
    def form_valid(self, form):
        blog = form.save(commit = False)
        blog.user = self.request.user
        blog.save()
        messages.success(self.request, 'ブログを作成しました。')
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'ブログの投稿に失敗しました。')
        return super().form_invalid(form)   
    
class BlogUpdateView(LoginRequiredMixin, OnlyYouMixin, generic.UpdateView):
    model = Post
    template_name = 'blog_update.html'
    form_class = BlogCreateForm
    
    def get_success_url(self):
        return reverse_lazy('blog:blog_detail', kwargs = {'pk': self.kwargs['pk']})
    
    def form_valid(self, form):
        messages.success(self.request, '投稿を更新しました。')
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, '投稿の更新に失敗しました。')
        return super().form_invalid(form)
    
class BlogDeleteView(LoginRequiredMixin, OnlyYouMixin, generic.DeleteView):
    model = Post
    template_name = 'blog_delete.html'
    success_url = reverse_lazy('blog:blog_list')

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, '投稿を削除しました。')
        return super().delete(request, *args, **kwargs)


class BlogSearchView(generic.ListView):
    model = Post
    template_name = 'blog_search.html'
    context_object_name = 'blog_list'

    def get_queryset(self):
        query = super().get_queryset()
        title = self.request.GET.get('title', None)
        if title:
            query = query.filter(title__icontains = title)
        return query
   
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = self.request.GET.get('title', '')
        return context