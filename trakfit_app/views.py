from django.shortcuts import render

def login(request):
    return render(request, 'login.html')

def logout(request):
    return render(request, 'login.html')

def register(request):
    return render(request, 'register.html')

def resetPassword(request):
    return render(request, 'reset_password.html')

def forgot_password(request):
    return render(request, 'forgot-password.html')

def enter_code(request):
    return render(request, 'enter-code.html')

def teacher_dashboard(request):
    return render(request, 'teacher-dashboard.html')

def student_management(request):
    return render(request, 'student-management.html')

def student_profile(request, student_id):
    return render(request, 'student-profile.html')

def change_password(request):
    return render(request, 'change-password.html')