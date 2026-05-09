from django.contrib import admin
from .models import UserProfile, Entry, LibraryItem, ReadingProgress, IntentTimer, VisionBoard, VisionBoardImage, RegistrationRequest, BroadcastMessage, GroupTimer, GroupReadingSession, CommunityPrayer

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'role', 'personal_email']

@admin.register(Entry)
class EntryAdmin(admin.ModelAdmin):
    list_display = ['user', 'category', 'is_private', 'is_answered', 'created_at']
    list_filter = ['category', 'is_private', 'is_answered']

@admin.register(LibraryItem)
class LibraryItemAdmin(admin.ModelAdmin):
    list_display = ['title', 'media_type', 'access_level', 'owner', 'added_at']
    list_filter = ['media_type', 'access_level']

@admin.register(ReadingProgress)
class ReadingProgressAdmin(admin.ModelAdmin):
    list_display = ['user', 'item', 'current_page', 'progress_pct', 'last_read']

@admin.register(IntentTimer)
class IntentTimerAdmin(admin.ModelAdmin):
    list_display = ['user', 'title', 'duration_minutes', 'completed']

@admin.register(VisionBoard)
class VisionBoardAdmin(admin.ModelAdmin):
    list_display = ['owner', 'name', 'is_public', 'created_at']
    prepopulated_fields = {'slug': ('name',)}

admin.site.register(VisionBoardImage)

@admin.register(RegistrationRequest)
class RegistrationRequestAdmin(admin.ModelAdmin):
    list_display = ['user', 'status', 'requested_at', 'reviewed_by']
    list_filter = ['status']
    actions = ['approve_users', 'deny_users']

    def approve_users(self, request, queryset):
        for reg in queryset:
            reg.status = 'APPROVED'
            reg.user.is_active = True
            reg.user.save()
            reg.save()
    approve_users.short_description = 'Approve selected requests'

    def deny_users(self, request, queryset):
        for reg in queryset:
            reg.status = 'DENIED'
            reg.user.is_active = False
            reg.user.save()
            reg.save()
    deny_users.short_description = 'Deny selected requests'

admin.site.register(BroadcastMessage)
admin.site.register(GroupTimer)
admin.site.register(GroupReadingSession)
admin.site.register(CommunityPrayer)
