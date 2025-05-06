from django.contrib import admin
from .models import UserPreference, UserInterest, UserInterestRelation, Match

@admin.register(UserPreference)
class UserPreferenceAdmin(admin.ModelAdmin):
    list_display = ('user', 'min_age', 'max_age', 'max_distance', 'gender_preference')
    list_filter = ('gender_preference',)
    search_fields = ('user__username',)

@admin.register(UserInterest)
class UserInterestAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(UserInterestRelation)
class UserInterestRelationAdmin(admin.ModelAdmin):
    list_display = ('user', 'interest')
    list_filter = ('interest',)
    search_fields = ('user__username', 'interest__name')

@admin.register(Match)
class MatchAdmin(admin.ModelAdmin):
    list_display = ('user1', 'user2', 'created_at', 'is_active')
    list_filter = ('is_active', 'created_at')
    search_fields = ('user1__username', 'user2__username')
