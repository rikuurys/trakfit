from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import IntegrityError
from datetime import datetime
from .models import User, Student


def login(request):
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        
        if not email or not password:
            messages.error(request, 'Please enter both email and password.')
            return render(request, 'login.html')
        
        # Authenticate user
        user = authenticate(request, username=email, password=password)
        
        if user is not None:
            # Check if user has a student profile (student-only login)
            if hasattr(user, 'student_profile'):
                auth_login(request, user)
                messages.success(request, f'Welcome back, {user.student_profile.first_name}!')
                return redirect('student-dashboard')
            else:
                messages.error(request, 'Only students can login through this portal.')
                return render(request, 'login.html')
        else:
            messages.error(request, 'Invalid email or password.')
            return render(request, 'login.html')
    
    return render(request, 'login.html')


def logout(request):
    auth_logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('login')


def register(request):
    if request.method == 'POST':
        # Extract form data
        student_no = request.POST.get('student_no', '').strip()
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        birthday = request.POST.get('birthday', '').strip()
        year_level = request.POST.get('year_level', '').strip()
        section_code = request.POST.get('section_code', '').strip()
        email = request.POST.get('email', '').strip()
        gender = request.POST.get('gender', '')
        password = request.POST.get('password', '')
        confirm_password = request.POST.get('confirm_password', '')
        
        # Validation
        errors = []
        
        if not all([student_no, first_name, last_name, birthday, year_level, section_code, email, gender, password]):
            errors.append('All fields are required.')
        
        if password != confirm_password:
            errors.append('Passwords do not match.')
        
        if len(password) < 8:
            errors.append('Password must be at least 8 characters long.')
        
        # Validate email format
        if email and '@' not in email:
            errors.append('Invalid email format.')
        
        # Calculate age from birthday
        try:
            birth_date = datetime.strptime(birthday, '%Y-%m-%d')
            today = datetime.today()
            age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
            
            if age < 5 or age > 100:
                errors.append('Invalid age.')
        except ValueError:
            errors.append('Invalid date format.')
            age = None
        
        # Check for duplicate email
        if User.objects.filter(email=email).exists():
            errors.append('Email already registered.')
        
        # Check for duplicate student number
        if Student.objects.filter(student_no=student_no).exists():
            errors.append('Student number already exists.')
        
        if errors:
            for error in errors:
                messages.error(request, error)
            return render(request, 'register.html')
        
        try:
            # Create User
            user = User.objects.create_user(
                email=email,
                password=password
            )
            
            # Create Student profile
            student = Student.objects.create(
                user=user,
                student_no=student_no,
                first_name=first_name,
                last_name=last_name,
                age=age,
                section_code=section_code,
            )
            
            # Auto-login the user
            auth_login(request, user)
            messages.success(request, 'Registration successful! Welcome to TrakFit.')
            return redirect('student-dashboard')
            
        except IntegrityError as e:
            messages.error(request, 'An error occurred during registration. Please try again.')
            return render(request, 'register.html')
        except Exception as e:
            messages.error(request, f'An unexpected error occurred: {str(e)}')
            return render(request, 'register.html')
    
    return render(request, 'register.html')

def resetPassword(request):
    return render(request, 'reset_password.html')

def forgot_password(request):
    return render(request, 'forgot-password.html')

def enter_code(request):
    return render(request, 'enter-code.html')

@login_required
def student_dashboard(request):
    student = request.user.student_profile
    context = {
        'student': student,
        'full_name': f"{student.first_name} {student.last_name}",
        'first_name': student.first_name
    }
    return render(request, 'student/dashboard.html', context)

@login_required
def student_profile_view(request):
    student = request.user.student_profile
    latest_test = student.fitness_tests.order_by('-taken_at').first()
    
    context = {
        'student': student,
        'latest_test': latest_test,
        'full_name': f"{student.first_name} {student.last_name}",
    }
    return render(request, 'student/profile.html', context)

@login_required
def student_profile_update_view(request):
    from .models import FitnessTest
    from django.utils import timezone
    
    student = request.user.student_profile
    pre_test = student.fitness_tests.filter(test_type='pre').order_by('-taken_at').first()
    
    if request.method == 'POST':
        test_type = request.POST.get('test_type', 'post')  # Default to post, but allow pre
        
        # Parse form data
        height_cm = request.POST.get('height_cm')
        weight_kg = request.POST.get('weight_kg')
        vo2_distance_m = request.POST.get('vo2_distance_m')
        flexibility_cm = request.POST.get('flexibility_cm')
        strength_reps = request.POST.get('strength_reps')
        agility_sec = request.POST.get('agility_sec')
        speed_sec = request.POST.get('speed_sec')
        endurance_time = request.POST.get('endurance_time')  # mm:ss format
        
        try:
            # Create fitness test
            fitness_test = FitnessTest.objects.create(
                student=student,
                test_type=test_type,
                height_cm=height_cm if height_cm else None,
                weight_kg=weight_kg if weight_kg else None,
                vo2_distance_m=vo2_distance_m if vo2_distance_m else None,
                flexibility_cm=flexibility_cm if flexibility_cm else None,
                strength_reps=int(strength_reps) if strength_reps else None,
                agility_sec=agility_sec if agility_sec else None,
                speed_sec=speed_sec if speed_sec else None,
                taken_at=timezone.now()
            )
            
            # Parse and set endurance time
            if endurance_time:
                fitness_test.set_endurance_from_string(endurance_time)
                fitness_test.save()
            
            messages.success(request, f'{test_type.capitalize()} test saved successfully!')
            return redirect('student-profile')
            
        except Exception as e:
            messages.error(request, f'Error saving test: {str(e)}')
    
    context = {
        'student': student,
        'pre_test': pre_test,
        'full_name': f"{student.first_name} {student.last_name}",
    }
    return render(request, 'student/profile_update.html', context)

@login_required
def student_settings_view(request):
    return render(request, 'student/settings.html')

def teacher_dashboard(request):
    return render(request, 'teacher-dashboard.html')

def student_management(request):
    return render(request, 'student-management.html')

def student_profile(request, student_id):
    return render(request, 'student-profile.html')

def change_password(request):
    return render(request, 'change-password.html')