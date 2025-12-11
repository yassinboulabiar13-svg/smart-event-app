from django.contrib import admin
from .models import PrivateEvent, PublicEvent, Guest, UserProfile, ContactMessage

@admin.register(PrivateEvent)
class PrivateEventAdmin(admin.ModelAdmin):
    list_display = ('title', 'owner', 'date', 'location')

@admin.register(PublicEvent)
class PublicEventAdmin(admin.ModelAdmin):
    list_display = ('title', 'owner', 'date', 'location')

@admin.register(Guest)
class GuestAdmin(admin.ModelAdmin):
    list_display = ('email', 'status', 'event_private', 'event_public')

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone')

@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'created_at')
