from django.contrib import admin
from .models import RequestLog


@admin.register(RequestLog)
class RequestLogAdmin(admin.ModelAdmin):
    # Columns to display in the list view
    list_display = (
        'method',
        'path',
        'user',
        'user_id',
        'ip_address',
        'status_code',
        'error_message',
        'response_time_ms',
        'user_agent',
        'device_info',
        'created_at'
    )

    # Fields you can filter by
    list_filter = ('method', 'status_code', 'error_message','created_at','device_info',)

    # Fields to search in the admin
    search_fields = ('path', 'user', 'user_id', 'device_info','ip_address')

    # Order by most recent first
    ordering = ('-created_at',)

    # Make all fields read-only (recommended for logs)
    readonly_fields = (
        'method',
        'path',
        'user',
        'user_id',
        'ip_address',
        'query_params',
        'error_message',
        'body',
        'status_code',
        'response_time_ms',
        'user_agent',
        'device_info',
        'created_at'
    )