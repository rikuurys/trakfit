from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from decimal import Decimal


class UserManager(BaseUserManager):
    """Custom user manager for email-based authentication."""
    
    def create_user(self, email, password=None, **extra_fields):
        """Create and save a regular user with the given email and password."""
        if not email:
            raise ValueError('Email is required')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, password=None, **extra_fields):
        """Create and save a superuser with the given email and password."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """Custom user model with email as login identifier."""
    
    email = models.EmailField(unique=True)
    is_active = models.BooleanField(default=True)
    last_login_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Required for Django admin and permissions
    is_staff = models.BooleanField(default=False)
    
    objects = UserManager()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []
    
    class Meta:
        db_table = 'users'
    
    def __str__(self):
        return self.email


class Student(models.Model):
    """Student profile linked to User."""
    
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name='student_profile'
    )
    student_no = models.CharField(max_length=50, unique=True)
    first_name = models.CharField(max_length=100)
    middle_initial = models.CharField(max_length=5, blank=True, null=True)
    last_name = models.CharField(max_length=100)
    age = models.IntegerField()
    gender = models.CharField(max_length=10, blank=True, null=True)
    section_code = models.CharField(max_length=20)
    group_code = models.CharField(max_length=20, help_text="Student's assigned group code (e.g., G1, G2, G3)")
    last_data_update_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'students'
    
    def __str__(self):
        return f"{self.student_no} - {self.first_name} {self.last_name}"


class FitnessTest(models.Model):
    """Fitness test records for students (pre or post test)."""
    
    TEST_TYPE_CHOICES = [
        ('pre', 'Pre Test'),
        ('post', 'Post Test'),
    ]
    
    test_id = models.AutoField(primary_key=True)
    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        db_column='student_id',
        related_name='fitness_tests'
    )
    test_type = models.CharField(max_length=10, choices=TEST_TYPE_CHOICES)
    height_cm = models.DecimalField(
        max_digits=5, 
        decimal_places=1, 
        null=True, 
        blank=True,
        validators=[MinValueValidator(Decimal('100')), MaxValueValidator(Decimal('250'))]
    )
    weight_kg = models.DecimalField(
        max_digits=5, 
        decimal_places=1, 
        null=True, 
        blank=True,
        validators=[MinValueValidator(Decimal('30')), MaxValueValidator(Decimal('200'))]
    )
    vo2_distance_m = models.DecimalField(
        max_digits=7, 
        decimal_places=1, 
        null=True, 
        blank=True,
        validators=[MinValueValidator(Decimal('500')), MaxValueValidator(Decimal('5000'))]
    )
    flexibility_cm = models.DecimalField(
        max_digits=5, 
        decimal_places=1, 
        null=True, 
        blank=True,
        validators=[MinValueValidator(Decimal('-20')), MaxValueValidator(Decimal('50'))]
    )
    strength_reps = models.IntegerField(
        null=True, 
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(200)]
    )
    agility_sec = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        null=True, 
        blank=True,
        validators=[MinValueValidator(Decimal('5')), MaxValueValidator(Decimal('60'))]
    )
    speed_sec = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        null=True, 
        blank=True,
        validators=[MinValueValidator(Decimal('4')), MaxValueValidator(Decimal('20'))]
    )
    endurance_minutes = models.IntegerField(
        null=True, 
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(99)]
    )
    endurance_seconds = models.IntegerField(
        null=True, 
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(59)]
    )
    taken_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    remarks = models.TextField(null=True, blank=True)
    remarksCreated= models.DateTimeField(blank=True, null=True)
    
    class Meta:
        db_table = 'fitness_tests'
    
    def clean(self):
        """Validate endurance seconds is between 0-59."""
        super().clean()
        if self.endurance_seconds is not None and (self.endurance_seconds < 0 or self.endurance_seconds > 59):
            raise ValidationError({'endurance_seconds': 'Seconds must be between 0 and 59.'})
    
    @property
    def bmi(self):
        """Calculate BMI from height and weight. Returns None if data is missing."""
        if self.height_cm and self.weight_kg:
            height_m = float(self.height_cm) / 100
            weight = float(self.weight_kg)
            return weight / (height_m ** 2)
        return None
    
    @property
    def vo2_max(self):
        """Calculate VO2 Max using Cooper formula. Returns None if distance is missing."""
        if self.vo2_distance_m:
            return (float(self.vo2_distance_m) - 504.9) / 44.73
        return None
    
    def get_endurance_display(self):
        """Return endurance formatted as mm:ss string."""
        if self.endurance_minutes is not None and self.endurance_seconds is not None:
            return f"{self.endurance_minutes:02d}:{self.endurance_seconds:02d}"
        return None
    
    def set_endurance_from_string(self, time_str):
        """Parse mm:ss string and set endurance_minutes and endurance_seconds."""
        if time_str and ':' in time_str:
            parts = time_str.split(':')
            if len(parts) == 2:
                try:
                    self.endurance_minutes = int(parts[0])
                    self.endurance_seconds = int(parts[1])
                except ValueError:
                    raise ValidationError('Invalid time format. Use mm:ss.')
    
    def __str__(self):
        return f"{self.student.student_no} - {self.test_type} ({self.taken_at})"


# class Remark(models.Model):
#     """Remarks/feedback for students on their fitness tests."""
#
#     student = models.ForeignKey(
#         Student,
#         on_delete=models.CASCADE,
#         db_column='student_id',
#         related_name='remarks'
#     )
#     test = models.ForeignKey(
#         FitnessTest,
#         on_delete=models.CASCADE,
#         db_column='test_id',
#         related_name='remarks'
#     )
#     body = models.TextField()
#     created_at = models.DateTimeField(auto_now_add=True)
#
#     class Meta:
#         db_table = 'remarks'
#
#     def __str__(self):
#         return f"Remark for {self.student.student_no} on test {self.test.test_id}"
