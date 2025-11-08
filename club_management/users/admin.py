from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    model = CustomUser

    # Columns shown in the user list
    list_display = (
        'personal_email', 'username', 'role', 'course', 'year',
        'branch', 'enrollment_number', 'is_staff', 'is_active'
    )
    
    # Filters on the right side
    list_filter = ('role', 'course', 'year', 'is_staff', 'is_active')

    # Field arrangement on the edit page
    fieldsets = (
        (None, {'fields': ('personal_email', 'password')}),
        ('Personal Info', {'fields': ('username', 'first_name', 'last_name', 'phone', 'profile_picture')}),
        ('Academic Info', {'fields': ('college_email', 'course', 'year', 'branch', 'enrollment_number')}),
        ('Role & Permissions', {'fields': ('role', 'is_staff', 'is_active', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important Dates', {'fields': ('last_login', 'date_joined')}),
    )

    # Fields used when creating a new user
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'personal_email', 'username', 'role', 'password1', 'password2',
                'course', 'year', 'branch', 'enrollment_number', 'is_staff', 'is_active'
            ),
        }),
    )

    search_fields = ('personal_email', 'username', 'college_email', 'enrollment_number')
    ordering = ('personal_email',)
