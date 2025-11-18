from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Student, FitnessTest


class UserAdmin(BaseUserAdmin):
    """Custom admin for User model."""
    list_display = ('email', 'is_active', 'is_staff', 'is_superuser', 'created_at')
    list_filter = ('is_active', 'is_staff', 'is_superuser')
    search_fields = ('email',)
    ordering = ('-created_at',)
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'last_login_at', 'created_at', 'updated_at')}),
    )
    
    readonly_fields = ('created_at', 'updated_at', 'last_login')
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'is_active', 'is_staff', 'is_superuser'),
        }),
    )


class StudentAdmin(admin.ModelAdmin):
    """Admin for Student model."""
    list_display = ('student_no', 'first_name', 'last_name', 'age', 'section_code', 'created_at')
    list_filter = ('section_code', 'age')
    search_fields = ('student_no', 'first_name', 'last_name', 'user__email')
    ordering = ('-created_at',)
    
    fieldsets = (
        ('User Account', {'fields': ('user',)}),
        ('Personal Information', {'fields': ('student_no', 'first_name', 'middle_initial', 'last_name', 'age')}),
        ('Academic Information', {'fields': ('section_code', 'group_code'), 'description': 'Group code is required for all students'}),
        ('Timestamps', {'fields': ('last_data_update_at', 'created_at', 'updated_at')}),
    )
    
    readonly_fields = ('created_at', 'updated_at')


class FitnessTestAdmin(admin.ModelAdmin):
    """Admin for FitnessTest model."""
    list_display = ('test_id', 'student', 'test_type', 'bmi', 'vo2_max', 'taken_at')
    list_filter = ('test_type', 'taken_at')
    search_fields = ('student__student_no', 'student__first_name', 'student__last_name')
    ordering = ('-taken_at',)
    
    fieldsets = (
        ('Test Information', {'fields': ('student', 'test_type', 'taken_at')}),
        ('Body Measurements', {'fields': ('height_cm', 'weight_kg', 'bmi')}),
        ('Fitness Metrics', {'fields': ('vo2_distance_m', 'vo2_max', 'flexibility_cm', 'strength_reps', 'agility_sec', 'speed_sec', 'endurance_min')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )
    
    readonly_fields = ('created_at', 'updated_at')


class RemarkAdmin(admin.ModelAdmin):
    """Admin for Remark model - DEPRECATED: Remarks now stored in FitnessTest.remarks field."""
    pass
    # list_display = ('id', 'student', 'test', 'created_at')
    # list_filter = ('created_at',)
    # search_fields = ('student__student_no', 'student__first_name', 'student__last_name', 'body')
    # ordering = ('-created_at',)
    # 
    # fieldsets = (
    #     ('Remark Information', {'fields': ('student', 'test', 'body')}),
    #     ('Timestamp', {'fields': ('created_at',)}),
    # )
    # 
    # readonly_fields = ('created_at',)


# Register models
admin.site.register(User, UserAdmin)
admin.site.register(Student, StudentAdmin)
admin.site.register(FitnessTest, FitnessTestAdmin)
# admin.site.register(Remark, RemarkAdmin)  # Deprecated - remarks now in FitnessTest model

