from django.contrib import admin
from .models import HamaliEntry


@admin.register(HamaliEntry)
class HamaliEntryAdmin(admin.ModelAdmin):
    list_display = ('entry_no', 'entry_date', 'party', 'item', 'hamali_type', 'amount')
    list_filter = ('entry_date', 'hamali_type')
    search_fields = ('party__client_name', 'item__itemname', 'entry_no', 'hamali_type')
    ordering = ('-entry_date', '-entry_no')
