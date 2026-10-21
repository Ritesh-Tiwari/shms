from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    pass



# from accounts.models import User
# from accounts.choices import UserRole

# user = User.objects.get(email="admin@gmail.com")
# user.role = UserRole.ADMIN
# user.save(update_fields=["role"])