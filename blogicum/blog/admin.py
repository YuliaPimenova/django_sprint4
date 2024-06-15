from django.contrib import admin

from .models import Category, Comment, Location, Post


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('title', 'description', 'is_published', 'created_at')
    search_fields = ('title', 'description')
    list_editable = ('description', 'is_published')
    list_filter = ('is_published', )


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'author', 'text', 'category',
                    'pub_date', 'location', 'is_published', 'created_at')
    list_display_links = ('title', )
    list_editable = ('category', 'is_published')
    search_fields = ('title', 'text')
    list_filter = ('is_published', 'category')
    empty_value_display = 'Не задано'


class PostInline(admin.StackedInline):
    model = Post
    extra = 0


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_published', 'created_at')
    list_editable = ('is_published', )
    inlines = (
        PostInline,
    )


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('text', 'post', 'created_at', 'author')
