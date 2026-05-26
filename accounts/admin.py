from django.contrib import admin

from django.contrib.auth.admin import (
    UserAdmin
)

from .models import User


# =====================================
# CUSTOM USER ADMIN
# =====================================

@admin.register(User)
class CustomUserAdmin(UserAdmin):

    model = User

    list_display = (

        'username',

        'email',

        'role',

        'restaurant',

        'branch',

        'status',

        'waiter_pin',

        'is_staff',

    )

    list_filter = (

        'role',

        'restaurant',

        'branch',

        'status',

        'is_staff',

    )

    fieldsets = (

        (

            'Authentication',

            {

                'fields': (

                    'username',

                    'password',

                )

            }

        ),

        (

            'Personal Info',

            {

                'fields': (

                    'first_name',

                    'last_name',

                    'email',

                    'phone',

                    'avatar',

                    'birth_date',

                    'address',

                    'emergency_contact',

                )

            }

        ),

        (

            'Company Info',

            {

                'fields': (

                    'restaurant',

                    'branch',

                    'role',

                    'employee_id',

                    'waiter_pin',

                    'salary',

                    'hire_date',

                    'status',

                )

            }

        ),

        (

            'Permissions',

            {

                'fields': (

                    'is_active',

                    'is_staff',

                    'is_superuser',

                    'groups',

                    'user_permissions',

                )

            }

        ),

        (

            'Activity',

            {

                'fields': (

                    'is_online',

                    'last_activity',

                    'last_login',

                    'date_joined',

                )

            }

        ),

        (

            'Notes',

            {

                'fields': (

                    'notes',

                )

            }

        ),

    )

    add_fieldsets = (

        (

            None,

            {

                'classes': (

                    'wide',

                ),

                'fields': (

                    'username',

                    'email',

                    'password1',

                    'password2',

                    'role',

                    'restaurant',

                    'branch',

                    'status',

                    'waiter_pin',

                    'is_staff',

                    'is_active',

                ),

            },

        ),

    )

    search_fields = (

        'username',

        'email',

        'employee_id',

    )

    ordering = (

        'username',

    )
