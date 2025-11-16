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

        if email == "admin@trakfit.com" and password == "admin123":
            return redirect('/teacher-dashboard/')

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
    if request.method == 'POST':
        auth_logout(request)
        messages.success(request, 'You have been logged out successfully.')
        return redirect('login')
    # Redirect GET requests to dashboard (shouldn't logout via GET for security)
    return redirect('student-dashboard')


def register(request):
    if request.method == 'POST':
        # Extract form data
        student_no = request.POST.get('student_no', '').strip()
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        birthday = request.POST.get('birthday', '').strip()
        section_code = request.POST.get('section_code', '').strip()
        group_code = request.POST.get('group_code', '').strip()
        email = request.POST.get('email', '').strip()
        gender = request.POST.get('gender', '')
        password = request.POST.get('password', '')
        confirm_password = request.POST.get('confirm_password', '')
        
        # Validation
        errors = []
        
        if not all([student_no, first_name, last_name, birthday, section_code, email, gender, password]):
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
                gender=gender,
                section_code=section_code,
                group_code=group_code if group_code else None,
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
    from datetime import datetime
    import json
    
    student = request.user.student_profile
    
    # Get latest test for BMI data
    latest_test = student.fitness_tests.order_by('-taken_at').first()
    
    # Get pre-test (only one per student)
    pre_test = student.fitness_tests.filter(test_type='pre').order_by('-taken_at').first()
    
    # Get latest post-test
    post_test = student.fitness_tests.filter(test_type='post').order_by('-taken_at').first()
    
    # Add BMI status if latest test exists
    if latest_test and latest_test.bmi:
        latest_test.bmi_status = get_bmi_status(latest_test.bmi)
    
    # Get all remarks for the student
    remarks_data = []
    remarks = student.remarks.select_related('test').order_by('-created_at')[:10]
    
    for remark in remarks:
        test = remark.test
        # Try to find the corresponding pre/post test for comparison
        if test.test_type == 'post':
            comparison_test = student.fitness_tests.filter(test_type='pre').order_by('-taken_at').first()
        else:
            comparison_test = student.fitness_tests.filter(test_type='post').order_by('-taken_at').first()
        
        # Determine which metric the remark is about (simplified - using first non-null value)
        metric_name = "General"
        pre_value = "N/A"
        post_value = "N/A"
        
        # Check various metrics to determine what was tested
        if test.flexibility_cm is not None:
            metric_name = "Flexibility (Sit & Reach)"
            if test.test_type == 'post' and comparison_test and comparison_test.flexibility_cm:
                pre_value = float(comparison_test.flexibility_cm)
                post_value = float(test.flexibility_cm)
            elif test.test_type == 'pre' and comparison_test and comparison_test.flexibility_cm:
                pre_value = float(test.flexibility_cm)
                post_value = float(comparison_test.flexibility_cm)
        elif test.strength_reps is not None:
            metric_name = "Strength (Push-ups)"
            if test.test_type == 'post' and comparison_test and comparison_test.strength_reps:
                pre_value = comparison_test.strength_reps
                post_value = test.strength_reps
            elif test.test_type == 'pre' and comparison_test and comparison_test.strength_reps:
                pre_value = test.strength_reps
                post_value = comparison_test.strength_reps
        elif test.vo2_distance_m is not None and test.vo2_max:
            metric_name = "VO₂ Max"
            if test.test_type == 'post' and comparison_test and comparison_test.vo2_max:
                pre_value = round(comparison_test.vo2_max, 1)
                post_value = round(test.vo2_max, 1)
            elif test.test_type == 'pre' and comparison_test and comparison_test.vo2_max:
                pre_value = round(test.vo2_max, 1)
                post_value = round(comparison_test.vo2_max, 1)
        
        remarks_data.append({
            'date': test.taken_at.strftime('%Y-%m-%d') if test.taken_at else 'N/A',
            'metric': metric_name,
            'pre': pre_value,
            'post': post_value,
            'remark': remark.body
        })
    
    # Calculate VO2 Max trend data (last 5 tests with VO2 data)
    vo2_tests = student.fitness_tests.exclude(vo2_distance_m__isnull=True).order_by('taken_at')[:5]
    vo2_dates = []
    vo2_values = []
    
    for test in vo2_tests:
        if test.vo2_max:
            # Format date as short month name
            date_str = test.taken_at.strftime('%b') if test.taken_at else 'N/A'
            vo2_dates.append(date_str)
            vo2_values.append(round(test.vo2_max, 1))
    
    # If no VO2 data, provide default empty arrays
    if not vo2_dates:
        vo2_dates = ['No Data']
        vo2_values = [0]
    
    # Calculate improvement percentages (if both pre and post exist)
    improvements = {}
    if pre_test and post_test:
        if pre_test.flexibility_cm and post_test.flexibility_cm:
            improvements['flexibility'] = round(
                ((float(post_test.flexibility_cm) - float(pre_test.flexibility_cm)) / float(pre_test.flexibility_cm)) * 100, 1
            )
        if pre_test.strength_reps and post_test.strength_reps:
            improvements['strength'] = round(
                ((post_test.strength_reps - pre_test.strength_reps) / pre_test.strength_reps) * 100, 1
            )
        if pre_test.agility_sec and post_test.agility_sec:
            # For agility/speed, lower is better, so reverse the calculation
            improvements['agility'] = round(
                ((float(pre_test.agility_sec) - float(post_test.agility_sec)) / float(pre_test.agility_sec)) * 100, 1
            )
        if pre_test.speed_sec and post_test.speed_sec:
            improvements['speed'] = round(
                ((float(pre_test.speed_sec) - float(post_test.speed_sec)) / float(pre_test.speed_sec)) * 100, 1
            )
        if pre_test.endurance_minutes and post_test.endurance_minutes:
            pre_total_sec = (pre_test.endurance_minutes * 60) + (pre_test.endurance_seconds or 0)
            post_total_sec = (post_test.endurance_minutes * 60) + (post_test.endurance_seconds or 0)
            if pre_total_sec > 0:
                improvements['endurance'] = round(
                    ((post_total_sec - pre_total_sec) / pre_total_sec) * 100, 1
                )
    
    context = {
        'student': student,
        'full_name': f"{student.first_name} {student.last_name}",
        'first_name': student.first_name,
        'latest_test': latest_test,
        'pre_test': pre_test,
        'post_test': post_test,
        'remarks_json': json.dumps(remarks_data),
        'vo2_dates_json': json.dumps(vo2_dates),
        'vo2_values_json': json.dumps(vo2_values),
        'improvements': improvements,
    }
    return render(request, 'student/dashboard.html', context)

@login_required
def student_profile_view(request):
    student = request.user.student_profile
    latest_test = student.fitness_tests.order_by('-taken_at').first()
    
    # Add BMI status if latest test exists
    if latest_test and latest_test.bmi:
        latest_test.bmi_status = get_bmi_status(latest_test.bmi)
    
    # Calculate test counts
    pre_test_count = student.fitness_tests.filter(test_type='pre').count()
    post_test_count = student.fitness_tests.filter(test_type='post').count()
    
    # Get pre-test for button lock check
    pre_test = student.fitness_tests.filter(test_type='pre').order_by('-taken_at').first()
    
    context = {
        'student': student,
        'latest_test': latest_test,
        'full_name': f"{student.first_name} {student.last_name}",
        'pre_test_count': pre_test_count,
        'post_test_count': post_test_count,
        'pre_test': pre_test,
    }
    return render(request, 'student/profile.html', context)

@login_required
def student_profile_update_view(request):
    """Legacy view - redirects to appropriate test entry page"""
    test_type = request.GET.get('test_type', 'post')
    if test_type == 'pre':
        return redirect('student-pre-test')
    else:
        return redirect('student-post-test')

@login_required
def student_pre_test_view(request):
    from .models import FitnessTest
    from django.utils import timezone
    
    student = request.user.student_profile
    
    if request.method == 'POST':
        test_type = 'pre'  # Force pre test type
        
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
            
            messages.success(request, 'Pre-test saved successfully!')
            return redirect('student-profile')
            
        except Exception as e:
            messages.error(request, f'Error saving pre-test: {str(e)}')
    
    context = {
        'student': student,
        'full_name': f"{student.first_name} {student.last_name}",
    }
    return render(request, 'student/pre_test.html', context)

@login_required
def student_post_test_view(request):
    from .models import FitnessTest
    from django.utils import timezone
    
    student = request.user.student_profile
    pre_test = student.fitness_tests.filter(test_type='pre').order_by('-taken_at').first()
    
    if request.method == 'POST':
        test_type = 'post'  # Force post test type
        
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
            
            messages.success(request, 'Post-test saved successfully!')
            return redirect('student-profile')
            
        except Exception as e:
            messages.error(request, f'Error saving post-test: {str(e)}')
    
    context = {
        'student': student,
        'pre_test': pre_test,
        'full_name': f"{student.first_name} {student.last_name}",
    }
    return render(request, 'student/post_test.html', context)

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

def get_bmi_status(bmi):
    """Helper function to categorize BMI"""
    if bmi is None:
        return 'N/A'
    if bmi < 18.5:
        return 'Underweight'
    elif bmi < 25:
        return 'Normal'
    elif bmi < 30:
        return 'Overweight'
    else:
        return 'Obese'

@login_required
def student_history(request):
    from datetime import datetime
    
    student = request.user.student_profile
    
    # Get all fitness tests for the student
    tests = student.fitness_tests.all().order_by('-taken_at')
    
    # Apply filters
    test_type = request.GET.get('test_type', 'all')
    start_date = request.GET.get('start_date', '')
    end_date = request.GET.get('end_date', '')
    
    # Filter by test type
    if test_type and test_type != 'all':
        tests = tests.filter(test_type=test_type)
    
    # Filter by date range
    if start_date:
        try:
            start_dt = datetime.strptime(start_date, '%Y-%m-%d')
            tests = tests.filter(taken_at__date__gte=start_dt.date())
        except ValueError:
            pass
    
    if end_date:
        try:
            end_dt = datetime.strptime(end_date, '%Y-%m-%d')
            tests = tests.filter(taken_at__date__lte=end_dt.date())
        except ValueError:
            pass
    
    # Add BMI status to each test
    tests_with_status = []
    for test in tests:
        test.bmi_status = get_bmi_status(test.bmi)
        tests_with_status.append(test)
    
    # Get pre-test for button lock check
    pre_test = student.fitness_tests.filter(test_type='pre').order_by('-taken_at').first()
    
    context = {
        'student': student,
        'tests': tests_with_status,
        'test_type_filter': test_type,
        'start_date_filter': start_date,
        'end_date_filter': end_date,
        'full_name': f"{student.first_name} {student.last_name}",
        'pre_test': pre_test,
    }
    return render(request, 'student/history.html', context)