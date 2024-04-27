from django.contrib import admin
from users.models import Subscriptions, MyUser


@admin.register(MyUser)
class UserAdmin(admin.ModelAdmin):
    list_display = ('email', 'username', 'first_name', 'last_name')
    list_filter = ('email', 'first_name')


admin.site.register(Subscriptions)
