
from django.contrib import admin

from .models import Task


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):

    list_display = (
        'title',
        'owner',
        'priority',
        'status',
        'due_date',
        'created_at',
    )

    list_filter = (
        'owner',
        'priority',
        'status',
        'created_at',
    )

    search_fields = (
        'title',
        'description',
        'owner__username',
        'owner__email',
    )

    list_editable = (
        'priority',
        'status',
    )

    ordering = ('-created_at',)

    readonly_fields = (
        'created_at',
        'updated_at',
    )
