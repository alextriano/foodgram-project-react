from django.contrib import admin

from .models import User

admin.site.empty_value_display = 'Не задано'


class UserAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'email',
        'username',
        'first_name',
        'last_name'
    )
    list_editable = (
        'email',
        'username',
        'first_name',
        'last_name'
    )
    list_filter = (
        'email',
        'username'
    )
    search_fields = (
        'id',
        'email',
        'username',
        'first_name',
        'last_name'
    )
    ordering = ['id']


admin.site.register(User, UserAdmin)
