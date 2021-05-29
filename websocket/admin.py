from django.contrib import admin
from .models import User, Chat


class UserAdmin(admin.ModelAdmin):

    list_display = ['uuid', 'username', 'is_staff', 'is_superuser']
    search_fields = ['uuid', 'username']
    list_filter = ['is_staff', 'is_superuser']

    def save_model(self, request, obj, form, change):
        # Override for being able to change users passwords
        obj.set_password(obj.password)
        return super(UserAdmin, self).save_model(request, obj, form, change)


admin.site.register(Chat)
admin.site.register(User, UserAdmin)
