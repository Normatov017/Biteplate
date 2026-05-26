from django.contrib import admin

from .models import Role
from .models import Permission
from .models import RolePermission


admin.site.register(Role)
admin.site.register(Permission)
admin.site.register(RolePermission)