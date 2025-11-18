"""
URL configuration for TrakFit project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from trakfit_app import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.login, name='login'),
    path('logout/', views.logout, name='logout'),
    path('register/', views.register, name='register'),
    path('register/pre-test/', views.pre_test_register, name='pre-test-register'),
    #path('reset-password/', views.resetPassword, name='resetPassword'),
    #path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('enter-code/', views.enter_code, name='enter_code'),
    path('student-dashboard/', views.student_dashboard, name='student-dashboard'),
    path('student-profile/', views.student_profile_view, name='student-profile'),
    path('student-profile-update/', views.student_profile_update_view, name='student-profile-update'),
    path('student-pre-test/', views.student_pre_test_view, name='student-pre-test'),
    path('student-post-test/', views.student_post_test_view, name='student-post-test'),
    path('student/test/update/<int:test_id>/', views.update_test_view, name='update-test'),
    path('student/test/remark/', views.add_remark, name='add-remark'),
    path('teacher-dashboard/', views.teacher_dashboard, name='teacher_dashboard'),
    path('student-management/', views.student_management, name='student_management'),
    path('student-profile/<str:student_no>/', views.student_profile, name='student_profile'),
    path('add-remark/', views.add_remark, name='add_remark'),
    path('change-password/', views.change_password, name='change_password'),
    path('student-history', views.student_history, name='student-history'),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS)

