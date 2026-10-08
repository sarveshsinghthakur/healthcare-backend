from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

User = get_user_model()


class UserAdmin(DjangoUserAdmin):
    ordering = ('email',)
    list_display = ('email', 'username', 'name', 'is_staff', 'is_active')
    search_fields = ('email', 'username', 'name')
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('name', 'username')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {'classes': ('wide',), 'fields': ('email', 'username', 'name', 'password1', 'password2')}),
    )


admin.site.register(User, UserAdmin)
