from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import IntegrityError
from datetime import datetime
from django.utils import timezone
from .models import User, Student, FitnessTest
from .forms import FitnessTestForm


def login(request):
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        
        if not email or not password:
            messages.error(request, 'Please enter both email and password.')
            return render(request, 'login.html')


        # Authenticate user (primary) - ModelBackend expects `username` param
        user = authenticate(request, username=email, password=password)

        # Fallback: if authenticate returns None, try direct lookup + password check
        # This helps when a custom auth backend is in use or the backend expects a different kwarg.
        if user is None:
            try:
                potential = User.objects.get(email=email)
                if potential.check_password(password):
                    user = potential
            except User.DoesNotExist:
                user = None

        if user is not None:
            # Allow admins (superuser or staff) to access teacher dashboard
            if user.is_superuser or user.is_staff:
                auth_login(request, user)
                return redirect('teacher_dashboard')
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
        
        if not all([student_no, first_name, last_name, birthday, section_code, group_code, email, gender, password]):
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
                group_code=group_code,
            )
            
            # Auto-login the user
            auth_login(request, user)
            
            # Store registration data in session for pre-test step
            request.session['registration_complete'] = True
            request.session['new_user_id'] = user.id
            
            messages.success(request, 'Registration successful! Welcome to TrakFit.')
            return redirect('pre-test-register')
            
        except IntegrityError as e:
            messages.error(request, 'An error occurred during registration. Please try again.')
            return render(request, 'register.html')
        except Exception as e:
            messages.error(request, f'An unexpected error occurred: {str(e)}')
            return render(request, 'register.html')
    
    return render(request, 'register.html')

def pre_test_register(request):
    """Handle pre-test submission during registration (optional)"""
    # Check if user just completed registration
    if not request.session.get('registration_complete'):
        # If no registration session, redirect to login
        return redirect('login')
    
    if request.method == 'POST':
        # Check if user skipped pre-test
        skip_pretest = request.POST.get('skip_pretest', 'false') == 'true'
        
        if skip_pretest:
            # Clear registration session and redirect to dashboard
            request.session.pop('registration_complete', None)
            request.session.pop('new_user_id', None)
            messages.info(request, 'You can add your pre-test data later from your profile.')
            return redirect('student-dashboard')
        
        # User submitted pre-test data
        student = request.user.student_profile
        
        try:
            # Extract and validate pre-test fields
            height_cm = request.POST.get('height_cm', '').strip()
            weight_kg = request.POST.get('weight_kg', '').strip()
            vo2_distance_m = request.POST.get('vo2_distance_m', '').strip()
            flexibility_cm = request.POST.get('flexibility_cm', '').strip()
            strength_reps = request.POST.get('strength_reps', '').strip()
            agility_sec = request.POST.get('agility_sec', '').strip()
            speed_sec = request.POST.get('speed_sec', '').strip()
            endurance_time = request.POST.get('endurance_time', '').strip()
            
            # Validate all fields are provided
            if not all([height_cm, weight_kg, vo2_distance_m, flexibility_cm, 
                       strength_reps, agility_sec, speed_sec, endurance_time]):
                messages.error(request, 'All fields are required for pre-test submission.')
                return render(request, 'student/pre_test_on_register.html')
            
            # Create fitness test
            fitness_test = FitnessTest.objects.create(
                student=student,
                test_type='pre',
                height_cm=height_cm,
                weight_kg=weight_kg,
                vo2_distance_m=vo2_distance_m,
                flexibility_cm=flexibility_cm,
                strength_reps=strength_reps,
                agility_sec=agility_sec,
                speed_sec=speed_sec,
                taken_at=timezone.now()
            )
            
            # Parse and set endurance time
            fitness_test.set_endurance_from_string(endurance_time)
            fitness_test.save()
            
            # Clear registration session
            request.session.pop('registration_complete', None)
            request.session.pop('new_user_id', None)
            
            messages.success(request, 'Pre-test completed successfully! Welcome to TrakFit.')
            return redirect('student-dashboard')
            
        except Exception as e:
            messages.error(request, f'Error saving pre-test: {str(e)}')
            return render(request, 'student/pre_test_on_register.html')
    
    # GET request - show pre-test form
    return render(request, 'student/pre_test_on_register.html')

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
    
    # Get all tests for the student (most recent first)
    remarks_data = []
    all_tests = student.fitness_tests.all().order_by('-taken_at')
    
    # Create a list of all tests with previous test data for comparison
    tests_list = list(all_tests)
    for i, test in enumerate(tests_list):
        # Find previous test (next in the list since ordered by -taken_at)
        previous_test = tests_list[i + 1] if i + 1 < len(tests_list) else None
        
        # Build test data with previous test comparison
        test_data = {
            'test_id': test.test_id,
            'test_type': test.get_test_type_display(),
            'test_type_key': test.test_type,
            'date': test.taken_at.strftime('%B %d, %Y') if test.taken_at else 'N/A',
            'bmi': round(test.bmi, 2) if test.bmi else None,
            'vo2_max': round(test.vo2_max, 2) if test.vo2_max else None,
            'remarks': test.remarks if test.remarks else None,
        }
        
        # Add previous test data for comparison
        if previous_test:
            test_data['previous_test'] = {
                'bmi': round(previous_test.bmi, 2) if previous_test.bmi else None,
                'vo2_max': round(previous_test.vo2_max, 2) if previous_test.vo2_max else None,
            }
        else:
            test_data['previous_test'] = None
        
        remarks_data.append(test_data)
    
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
    
    # Get pre-test for button lock check and comparison
    pre_test = student.fitness_tests.filter(test_type='pre').order_by('-taken_at').first()
    
    # Prepare comparison data for latest test
    pre_test_data = None
    previous_test_data = None
    
    if latest_test:
        # Build pre-test data
        if pre_test:
            pre_test_data = {
                'height_cm': float(pre_test.height_cm) if pre_test.height_cm else None,
                'weight_kg': float(pre_test.weight_kg) if pre_test.weight_kg else None,
                'bmi': round(pre_test.bmi, 1) if pre_test.bmi else None,
                'vo2_distance_m': float(pre_test.vo2_distance_m) if pre_test.vo2_distance_m else None,
                'vo2_max': round(pre_test.vo2_max, 1) if pre_test.vo2_max else None,
                'flexibility_cm': float(pre_test.flexibility_cm) if pre_test.flexibility_cm else None,
                'strength_reps': pre_test.strength_reps,
                'agility_sec': float(pre_test.agility_sec) if pre_test.agility_sec else None,
                'speed_sec': float(pre_test.speed_sec) if pre_test.speed_sec else None,
                'endurance_display': pre_test.get_endurance_display(),
            }
        
        # Get all tests ordered by date to find previous test
        all_tests_ordered = list(student.fitness_tests.all().order_by('-taken_at'))
        
        # Find previous test (the one before latest_test)
        try:
            current_test_index = next(i for i, t in enumerate(all_tests_ordered) if t.test_id == latest_test.test_id)
            if current_test_index + 1 < len(all_tests_ordered):
                previous_test = all_tests_ordered[current_test_index + 1]
                previous_test_data = {
                    'height_cm': float(previous_test.height_cm) if previous_test.height_cm else None,
                    'weight_kg': float(previous_test.weight_kg) if previous_test.weight_kg else None,
                    'bmi': round(previous_test.bmi, 1) if previous_test.bmi else None,
                    'vo2_distance_m': float(previous_test.vo2_distance_m) if previous_test.vo2_distance_m else None,
                    'vo2_max': round(previous_test.vo2_max, 1) if previous_test.vo2_max else None,
                    'flexibility_cm': float(previous_test.flexibility_cm) if previous_test.flexibility_cm else None,
                    'strength_reps': previous_test.strength_reps,
                    'agility_sec': float(previous_test.agility_sec) if previous_test.agility_sec else None,
                    'speed_sec': float(previous_test.speed_sec) if previous_test.speed_sec else None,
                    'endurance_display': previous_test.get_endurance_display(),
                }
        except StopIteration:
            pass
    
    context = {
        'student': student,
        'latest_test': latest_test,
        'full_name': f"{student.first_name} {student.last_name}",
        'pre_test_count': pre_test_count,
        'post_test_count': post_test_count,
        'pre_test': pre_test,
        'pre_test_data': pre_test_data,
        'previous_test_data': previous_test_data,
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
    form = FitnessTestForm()
    
    if request.method == 'POST':
        form = FitnessTestForm(request.POST)
        
        if form.is_valid():
            try:
                # Create fitness test with validated data
                fitness_test = FitnessTest.objects.create(
                    student=student,
                    test_type='pre',
                    height_cm=form.cleaned_data['height_cm'],
                    weight_kg=form.cleaned_data['weight_kg'],
                    vo2_distance_m=form.cleaned_data['vo2_distance_m'],
                    flexibility_cm=form.cleaned_data['flexibility_cm'],
                    strength_reps=form.cleaned_data['strength_reps'],
                    agility_sec=form.cleaned_data['agility_sec'],
                    speed_sec=form.cleaned_data['speed_sec'],
                    taken_at=timezone.now()
                )
                
                # Parse and set endurance time
                endurance_time = form.cleaned_data['endurance_time']
                fitness_test.set_endurance_from_string(endurance_time)
                fitness_test.save()
                
                messages.success(request, 'Pre-test saved successfully!')
                return redirect('student-profile')
                
            except Exception as e:
                messages.error(request, f'Error saving pre-test: {str(e)}')
        else:
            # Form validation failed - errors will be displayed in template
            messages.error(request, 'Please fix the errors below and try again.')
    
    context = {
        'student': student,
        'full_name': f"{student.first_name} {student.last_name}",
        'form': form,
    }
    return render(request, 'student/pre_test.html', context)

@login_required
def student_post_test_view(request):
    from .models import FitnessTest
    from django.utils import timezone
    
    student = request.user.student_profile
    pre_test = student.fitness_tests.filter(test_type='pre').order_by('-taken_at').first()
    form = FitnessTestForm()
    
    if request.method == 'POST':
        form = FitnessTestForm(request.POST)
        
        if form.is_valid():
            try:
                # Create fitness test with validated data
                fitness_test = FitnessTest.objects.create(
                    student=student,
                    test_type='post',
                    height_cm=form.cleaned_data['height_cm'],
                    weight_kg=form.cleaned_data['weight_kg'],
                    vo2_distance_m=form.cleaned_data['vo2_distance_m'],
                    flexibility_cm=form.cleaned_data['flexibility_cm'],
                    strength_reps=form.cleaned_data['strength_reps'],
                    agility_sec=form.cleaned_data['agility_sec'],
                    speed_sec=form.cleaned_data['speed_sec'],
                    taken_at=timezone.now()
                )
                
                # Parse and set endurance time
                endurance_time = form.cleaned_data['endurance_time']
                fitness_test.set_endurance_from_string(endurance_time)
                fitness_test.save()
                
                messages.success(request, 'Post-test saved successfully!')
                return redirect('student-profile')
                
            except Exception as e:
                messages.error(request, f'Error saving post-test: {str(e)}')
        else:
            # Form validation failed - errors will be displayed in template
            messages.error(request, 'Please fix the errors below and try again.')
    
    context = {
        'student': student,
        'pre_test': pre_test,
        'full_name': f"{student.first_name} {student.last_name}",
        'form': form,
    }
    return render(request, 'student/post_test.html', context)

@login_required
def update_test_view(request, test_id):
    """
    View to update an existing fitness test (post-tests only).
    """
    from .models import FitnessTest
    from django.utils import timezone
    
    student = request.user.student_profile
    
    # Get the test and verify ownership
    try:
        test = FitnessTest.objects.get(test_id=test_id)
    except FitnessTest.DoesNotExist:
        messages.error(request, "Test not found.")
        return redirect('student-history')

    # Verify the test belongs to the logged-in student
    if test.student != student:
        messages.error(request, "You do not have permission to edit this test.")
        return redirect('student-history')

    # Only allow editing post-tests
    if test.test_type != 'post':
        messages.error(request, "Only post-tests can be edited.")
        return redirect('student-history')

    if request.method == 'POST':
        form = FitnessTestForm(request.POST)
        
        if form.is_valid():
            try:
                # Update test fields with validated data
                test.height_cm = form.cleaned_data['height_cm']
                test.weight_kg = form.cleaned_data['weight_kg']
                test.vo2_distance_m = form.cleaned_data['vo2_distance_m']
                test.flexibility_cm = form.cleaned_data['flexibility_cm']
                test.strength_reps = form.cleaned_data['strength_reps']
                test.agility_sec = form.cleaned_data['agility_sec']
                test.speed_sec = form.cleaned_data['speed_sec']
                
                # Update endurance time
                endurance_time = form.cleaned_data['endurance_time']
                test.set_endurance_from_string(endurance_time)
                
                # Save (updated_at will be automatically updated by Django)
                test.save()

                messages.success(request, "Test record updated successfully!")
                return redirect('student-history')

            except Exception as e:
                messages.error(request, f"Error updating test: {str(e)}")
        else:
            # Form validation failed - errors will be displayed in template
            messages.error(request, 'Please fix the errors below and try again.')
    else:
        # GET request - initialize form with existing test data
        initial_data = {
            'height_cm': test.height_cm,
            'weight_kg': test.weight_kg,
            'vo2_distance_m': test.vo2_distance_m,
            'flexibility_cm': test.flexibility_cm,
            'strength_reps': test.strength_reps,
            'agility_sec': test.agility_sec,
            'speed_sec': test.speed_sec,
            'endurance_time': test.get_endurance_display(),
        }
        form = FitnessTestForm(initial=initial_data)

    # Get pre-test for comparison
    pre_test = student.fitness_tests.filter(test_type='pre').order_by('-taken_at').first()
    
    # Render the form with existing values
    context = {
        'student': student,
        'test': test,
        'pre_test': pre_test,
        'full_name': f"{student.first_name} {student.last_name}",
        'form': form,
    }
    return render(request, 'student/update_test.html', context)

@login_required
def teacher_dashboard(request):

    students= Student.objects.all()

    # Get Total Pre-Test and Post-Test for each student
    pre_total_bmi= 0
    post_total_bmi= 0

    pre_total_vo2= 0
    post_total_vo2= 0

    pre_total_flexibility= 0
    post_total_flexibility= 0

    pre_total_strength= 0
    post_total_strength= 0

    pre_total_agility= 0
    post_total_agility= 0

    pre_total_speed= 0
    post_total_speed= 0

    post_total_endurance= 0
    pre_total_endurance= 0

    bmi_change= 0

    sections= {}

    for i, stud in enumerate(students):

        sections= {
            f'{stud.section_code}-{stud.group_code}': None,
        }

        pre_test= stud.fitness_tests.filter(test_type='pre').order_by('-taken_at').first()
        post_test= stud.fitness_tests.filter(test_type='post').order_by('-taken_at').first()
        
        pre_total_bmi += pre_test.bmi if pre_test and pre_test.bmi else 0
        post_total_bmi += post_test.bmi if post_test and post_test.bmi else 0
        pre_total_vo2 += pre_test.vo2_max if pre_test and pre_test.vo2_max else 0
        post_total_vo2 += post_test.vo2_max if post_test and post_test.vo2_max else 0
        pre_total_flexibility += pre_test.flexibility_cm if pre_test and pre_test.flexibility_cm else 0
        post_total_flexibility += post_test.flexibility_cm if post_test and post_test.flexibility_cm else 0
        pre_total_strength += pre_test.strength_reps if pre_test and pre_test.strength_reps else 0
        post_total_strength += post_test.strength_reps if post_test and post_test.strength_reps else 0
        pre_total_agility += pre_test.agility_sec if pre_test and pre_test.agility_sec else 0
        post_total_agility += post_test.agility_sec if post_test and post_test.agility_sec else 0
        pre_total_speed += pre_test.speed_sec if pre_test and pre_test.speed_sec else 0
        post_total_speed += post_test.speed_sec if post_test and post_test.speed_sec else 0
        if pre_test and pre_test.endurance_minutes is not None:
            pre_total_endurance += (pre_test.endurance_minutes * 60) + (pre_test.endurance_seconds or 0)
        if post_test and post_test.endurance_minutes is not None:
            post_total_endurance += (post_test.endurance_minutes * 60) + (post_test.endurance_seconds or 0)
        
        bmi_change+= post_total_bmi - pre_total_bmi

    totalCount= students.count() if students.count() > 0 else 1  # Prevent division by zero
    average= {
        'bmi': {
            'pre': pre_total_bmi / totalCount,
            'post': post_total_bmi / totalCount,
        },
        'vo2_max': {
            'pre': pre_total_vo2 / totalCount,
            'post': post_total_vo2 / totalCount,
        },
        'flexibility_cm': {
            'pre': pre_total_flexibility / totalCount,
            'post': post_total_flexibility / totalCount,
        },
        'strength_reps': {
            'pre': pre_total_strength / totalCount,
            'post': post_total_strength / totalCount,
        },
        'agility_sec': {
            'pre': pre_total_agility / totalCount,
            'post': post_total_agility / totalCount,
        },
        'speed_sec': {
            'pre': pre_total_speed / totalCount,
            'post': post_total_speed / totalCount,
        },
        'endurance_sec': {
            'pre': pre_total_endurance / totalCount,
            'post': post_total_endurance / totalCount,
        },
        'bmi_change': bmi_change / totalCount,
    }

    context = {
        'average': average,
        'total_students': students.count(),
        'total_sections': len(sections),
    }

    return render(request, 'teacher-dashboard.html', context)

@login_required
def student_management(request):
    data = {
        'students': Student.objects.all(),
    }
    return render(request, 'student-management.html', data)

@login_required
def student_profile(request, student_no):
    from .models import FitnessTest
    
    student = Student.objects.get(student_no=student_no)
    
    # Get pre-test and post-test

    tests= student.fitness_tests.all().order_by('-taken_at')
    
    template = "student-profile.html"

    # Get pre-test (only one per student ever)
    pre_test = student.fitness_tests.filter(test_type='pre').order_by('-taken_at').first()
    post_test = student.fitness_tests.filter(test_type='post').order_by('-taken_at').first()
    
    # Compute endurance as decimal minutes (minutes + seconds/60) for chart rendering
    def _endurance_decimal(test):
        if not test:
            return None
        mins = test.endurance_minutes or 0
        secs = test.endurance_seconds or 0
        try:
            return float(mins) + (float(secs) / 60.0)
        except Exception:
            return None
    
    pre_endurance_decimal = _endurance_decimal(pre_test)
    post_endurance_decimal = _endurance_decimal(post_test)
    
    # Get all tests ordered by date for finding previous test
    all_tests_ordered = list(student.fitness_tests.all().order_by('-taken_at'))

    # Prepare test data with BMI, VO2 Max, remarks, pre-test, and previous test for JSON
    tests_data = []
    for idx, test in enumerate(tests):
        # Get remarks for this test

        # Build pre-test data
        pre_test_data = None
        if pre_test:
            pre_test_data = {
                'test_id': pre_test.test_id,
                'bmi': round(pre_test.bmi, 1) if pre_test.bmi else None,
                'vo2_max': round(pre_test.vo2_max, 1) if pre_test.vo2_max else None,
                'height_cm': float(pre_test.height_cm) if pre_test.height_cm else None,
                'weight_kg': float(pre_test.weight_kg) if pre_test.weight_kg else None,
                'flexibility_cm': float(pre_test.flexibility_cm) if pre_test.flexibility_cm else None,
                'strength_reps': pre_test.strength_reps,
                'agility_sec': float(pre_test.agility_sec) if pre_test.agility_sec else None,
                'speed_sec': float(pre_test.speed_sec) if pre_test.speed_sec else None,
                'endurance_display': pre_test.get_endurance_display(),
            }

        # Find previous test (the one taken before the current test)
        previous_test_data = None
        try:
            # Find the current test in the all_tests_ordered list
            current_test_index = next(i for i, t in enumerate(all_tests_ordered) if t.test_id == test.test_id)
            # Previous test is the next one in the list (since list is sorted by -taken_at)
            if current_test_index + 1 < len(all_tests_ordered):
                previous_test = all_tests_ordered[current_test_index + 1]
                previous_test_data = {
                    'test_id': previous_test.test_id,
                    'bmi': round(previous_test.bmi, 1) if previous_test.bmi else None,
                    'vo2_max': round(previous_test.vo2_max, 1) if previous_test.vo2_max else None,
                    'height_cm': float(previous_test.height_cm) if previous_test.height_cm else None,
                    'weight_kg': float(previous_test.weight_kg) if previous_test.weight_kg else None,
                    'flexibility_cm': float(previous_test.flexibility_cm) if previous_test.flexibility_cm else None,
                    'strength_reps': previous_test.strength_reps,
                    'agility_sec': float(previous_test.agility_sec) if previous_test.agility_sec else None,
                    'speed_sec': float(previous_test.speed_sec) if previous_test.speed_sec else None,
                    'endurance_display': previous_test.get_endurance_display(),
                }
        except StopIteration:
            pass

        test_dict = {
            'test_id': test.test_id,
            'test_type': test.get_test_type_display(),
            'test_type_key': test.test_type,
            'taken_at': test.taken_at.strftime('%B %d, %Y') if test.taken_at else 'N/A',
            'updated_at': test.updated_at.strftime('%B %d, %Y') if test.updated_at else 'N/A',
            'bmi': round(test.bmi, 1) if test.bmi else None,
            'vo2_max': round(test.vo2_max, 1) if test.vo2_max else None,
            'height_cm': float(test.height_cm) if test.height_cm else None,
            'weight_kg': float(test.weight_kg) if test.weight_kg else None,
            'flexibility_cm': float(test.flexibility_cm) if test.flexibility_cm else None,
            'strength_reps': test.strength_reps,
            'agility_sec': float(test.agility_sec) if test.agility_sec else None,
            'speed_sec': float(test.speed_sec) if test.speed_sec else None,
            'endurance_display': test.get_endurance_display(),
            'remarks': test.remarks,
            'remarksCreated': test.remarksCreated.strftime('%B %d, %Y') if test.remarksCreated else None,
            'pre_test': pre_test_data,
            'previous_test': previous_test_data,
        }
        tests_data.append(test_dict)

    import json
    
    data = {
        'student': student,
        'tests': tests,
        'pre_test': pre_test,
        'post_test': post_test,
        'pre_endurance_decimal': pre_endurance_decimal,
        'post_endurance_decimal': post_endurance_decimal,
        'tests_json': json.dumps(tests_data),
    }


    return render(request, template, data)

@login_required
def add_remark(request):
    """Handle remark submission via AJAX."""
    from .models import FitnessTest
    from django.http import JsonResponse
    from django.utils import timezone
    
    if request.method == 'POST':
        test_id = request.POST.get('test_id')
        remark_text = request.POST.get('remark', '').strip()
        
        if not test_id or not remark_text:
            return JsonResponse({'success': False, 'error': 'Missing test_id or remark text'})
        
        try:
            # Get the fitness test
            test = FitnessTest.objects.get(test_id=test_id)
            
            test.remarks = remark_text
            test.remarksCreated = timezone.now()
            test.save()
            
            return JsonResponse({
                'success': True,
                'remark': {
                    'body': remark_text,
                    'created_at': timezone.now().strftime('%B %d, %Y')
                }
            })
            
        except FitnessTest.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Test not found'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

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
    import json
    
    student = request.user.student_profile
    
    # Get all fitness tests for the student, sorted by latest first
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
    
    # Get pre-test (only one per student ever)
    pre_test = student.fitness_tests.filter(test_type='pre').order_by('-taken_at').first()

    # Get all tests ordered by date for finding previous test
    all_tests_ordered = list(student.fitness_tests.all().order_by('-taken_at'))
    
    # Prepare test data with BMI, VO2 Max, remarks, pre-test, and previous test for JSON
    tests_data = []
    for idx, test in enumerate(tests):
        # Get remarks for this test (now stored as text field)
        remarks_text = test.remarks if test.remarks else None
        
        # Build pre-test data
        pre_test_data = None
        if pre_test:
            pre_test_data = {
                'test_id': pre_test.test_id,
                'height_cm': float(pre_test.height_cm) if pre_test.height_cm else None,
                'weight_kg': float(pre_test.weight_kg) if pre_test.weight_kg else None,
                'bmi': round(pre_test.bmi, 1) if pre_test.bmi else None,
                'vo2_distance_m': float(pre_test.vo2_distance_m) if pre_test.vo2_distance_m else None,
                'vo2_max': round(pre_test.vo2_max, 1) if pre_test.vo2_max else None,
                'flexibility_cm': float(pre_test.flexibility_cm) if pre_test.flexibility_cm else None,
                'strength_reps': pre_test.strength_reps,
                'agility_sec': float(pre_test.agility_sec) if pre_test.agility_sec else None,
                'speed_sec': float(pre_test.speed_sec) if pre_test.speed_sec else None,
                'endurance_display': pre_test.get_endurance_display(),
            }
        
        # Find previous test (the one taken before the current test)
        previous_test_data = None
        try:
            # Find the current test in the all_tests_ordered list
            current_test_index = next(i for i, t in enumerate(all_tests_ordered) if t.test_id == test.test_id)
            # Previous test is the next one in the list (since list is sorted by -taken_at)
            if current_test_index + 1 < len(all_tests_ordered):
                previous_test = all_tests_ordered[current_test_index + 1]
                previous_test_data = {
                    'test_id': previous_test.test_id,
                    'height_cm': float(previous_test.height_cm) if previous_test.height_cm else None,
                    'weight_kg': float(previous_test.weight_kg) if previous_test.weight_kg else None,
                    'bmi': round(previous_test.bmi, 1) if previous_test.bmi else None,
                    'vo2_distance_m': float(previous_test.vo2_distance_m) if previous_test.vo2_distance_m else None,
                    'vo2_max': round(previous_test.vo2_max, 1) if previous_test.vo2_max else None,
                    'flexibility_cm': float(previous_test.flexibility_cm) if previous_test.flexibility_cm else None,
                    'strength_reps': previous_test.strength_reps,
                    'agility_sec': float(previous_test.agility_sec) if previous_test.agility_sec else None,
                    'speed_sec': float(previous_test.speed_sec) if previous_test.speed_sec else None,
                    'endurance_display': previous_test.get_endurance_display(),
                }
        except StopIteration:
            pass
        
        test_dict = {
            'test_id': test.test_id,
            'test_type': test.get_test_type_display(),
            'test_type_key': test.test_type,
            'taken_at': test.taken_at.strftime('%B %d, %Y') if test.taken_at else 'N/A',
            'updated_at': test.updated_at.strftime('%B %d, %Y') if test.updated_at else 'N/A',
            'height_cm': float(test.height_cm) if test.height_cm else None,
            'weight_kg': float(test.weight_kg) if test.weight_kg else None,
            'bmi': round(test.bmi, 1) if test.bmi else None,
            'vo2_distance_m': float(test.vo2_distance_m) if test.vo2_distance_m else None,
            'vo2_max': round(test.vo2_max, 1) if test.vo2_max else None,
            'flexibility_cm': float(test.flexibility_cm) if test.flexibility_cm else None,
            'strength_reps': test.strength_reps,
            'agility_sec': float(test.agility_sec) if test.agility_sec else None,
            'speed_sec': float(test.speed_sec) if test.speed_sec else None,
            'endurance_display': test.get_endurance_display(),
            'remarks': remarks_text,
            'remarksCreated': test.remarksCreated.strftime('%B %d, %Y at %I:%M %p') if test.remarksCreated else None,
            'pre_test': pre_test_data,
            'previous_test': previous_test_data,
        }
        tests_data.append(test_dict)
    
    context = {
        'student': student,
        'tests': tests,
        'tests_json': json.dumps(tests_data),
        'test_type_filter': test_type,
        'start_date_filter': start_date,
        'end_date_filter': end_date,
        'full_name': f"{student.first_name} {student.last_name}",
        'pre_test': pre_test,
    }
    return render(request, 'student/history.html', context)


# ADMIN SIDE!