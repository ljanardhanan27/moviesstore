from django.contrib import admin
from .models import Movie, Review

class MovieAdmin(admin.ModelAdmin):
    ordering = ['name']
    search_fields = ['name']
admin.site.register(Movie, MovieAdmin)
@admin.register(Review)

class ReviewAdmin(admin.ModelAdmin):
    list_display = ('id', 'movie', 'user', 'is_reported', 'date')
    list_filter = ('is_reported',)
    