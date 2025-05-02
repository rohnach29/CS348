from django.contrib import admin
from .models import Runner, Route, Run, Comment, RunLike

@admin.register(Runner)
class RunnerAdmin(admin.ModelAdmin):
    list_display = ('user', 'age', 'created_at')
    search_fields = ('user__username', 'user__email')

@admin.register(Route)
class RouteAdmin(admin.ModelAdmin):
    list_display = ('name', 'creator', 'distance_km', 'created_at')
    list_filter = ('creator',)
    search_fields = ('name', 'start_location', 'end_location')

@admin.register(Run)
class RunAdmin(admin.ModelAdmin):
    list_display = ('title', 'runner', 'date', 'distance_km', 'duration', 'is_public')
    list_filter = ('runner', 'date', 'is_public')
    search_fields = ('title', 'notes')
    date_hierarchy = 'date'

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('commenter', 'run', 'created_at')
    list_filter = ('commenter', 'run')

@admin.register(RunLike)
class RunLikeAdmin(admin.ModelAdmin):
    list_display = ('runner', 'run', 'created_at')
    list_filter = ('runner', 'run')
