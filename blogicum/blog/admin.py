from django.contrib import admin
from .models import Category
from .models import Post
from .models import Location

admin.site.register(Category)
admin.site.register(Location)
admin.site.register(Post)
