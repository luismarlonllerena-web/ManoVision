from django.contrib import admin
from .models import Event
@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('created_at','gesture','fingers','hands')
    list_filter = ('hands','fingers')
