from django.contrib import admin

from .models import (
    ActionAuditLog,
    Complaint,
    OrderHistoryLog
)

admin.site.register(
    OrderHistoryLog
)


@admin.register(ActionAuditLog)
class ActionAuditLogAdmin(admin.ModelAdmin):

    list_display = (
        'model_name',
        'object_id',
        'action',
        'user',
        'created_at',
    )

    list_filter = (
        'model_name',
        'action',
        'created_at',
    )

    search_fields = (
        'model_name',
        'object_id',
        'summary',
        'user__username',
    )


@admin.register(Complaint)
class ComplaintAdmin(admin.ModelAdmin):

    list_display = (
        'id',
        'table',
        'is_resolved',
        'resolved_by',
        'created_at',
    )

    list_filter = (
        'is_resolved',
        'created_at',
    )

    search_fields = (
        'description',
        'table__table_number',
    )
