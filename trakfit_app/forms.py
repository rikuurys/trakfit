from django import forms
from django.core.validators import MinValueValidator, MaxValueValidator, RegexValidator
from django.core.exceptions import ValidationError
from decimal import Decimal
import re


class FitnessTestForm(forms.Form):
    """Form for creating and updating fitness test records with client-matching validation."""
    
    # Body Metrics
    height_cm = forms.DecimalField(
        max_digits=5,
        decimal_places=1,
        validators=[
            MinValueValidator(Decimal('100'), message='Must be between 100 and 250'),
            MaxValueValidator(Decimal('250'), message='Must be between 100 and 250')
        ],
        required=True,
        error_messages={
            'required': 'This field is required',
            'invalid': 'Must be a valid number',
        },
        widget=forms.TextInput(attrs={
            'class': 'form-control form-input',
            'placeholder': 'Enter value...',
            'name': 'height_cm'
        })
    )
    
    weight_kg = forms.DecimalField(
        max_digits=5,
        decimal_places=1,
        validators=[
            MinValueValidator(Decimal('30'), message='Must be between 30 and 200'),
            MaxValueValidator(Decimal('200'), message='Must be between 30 and 200')
        ],
        required=True,
        error_messages={
            'required': 'This field is required',
            'invalid': 'Must be a valid number',
        },
        widget=forms.TextInput(attrs={
            'class': 'form-control form-input',
            'placeholder': 'Enter value...',
            'name': 'weight_kg'
        })
    )
    
    # VO2 Max
    vo2_distance_m = forms.DecimalField(
        max_digits=7,
        decimal_places=1,
        validators=[
            MinValueValidator(Decimal('500'), message='Must be between 500 and 5000'),
            MaxValueValidator(Decimal('5000'), message='Must be between 500 and 5000')
        ],
        required=True,
        error_messages={
            'required': 'This field is required',
            'invalid': 'Must be a valid number',
        },
        widget=forms.TextInput(attrs={
            'class': 'form-control form-input',
            'placeholder': 'Enter value...',
            'name': 'vo2_distance_m'
        })
    )
    
    # Fitness Profile
    flexibility_cm = forms.DecimalField(
        max_digits=5,
        decimal_places=1,
        validators=[
            MinValueValidator(Decimal('-20'), message='Must be between -20 and 50'),
            MaxValueValidator(Decimal('50'), message='Must be between -20 and 50')
        ],
        required=True,
        error_messages={
            'required': 'This field is required',
            'invalid': 'Must be a valid number',
        },
        widget=forms.TextInput(attrs={
            'class': 'form-control form-input',
            'placeholder': 'Enter value...',
            'name': 'flexibility_cm'
        })
    )
    
    strength_reps = forms.IntegerField(
        validators=[
            MinValueValidator(0, message='Must be between 0 and 200'),
            MaxValueValidator(200, message='Must be between 0 and 200')
        ],
        required=True,
        error_messages={
            'required': 'This field is required',
            'invalid': 'Must be a whole number',
        },
        widget=forms.TextInput(attrs={
            'class': 'form-control form-input',
            'placeholder': 'Enter value...',
            'name': 'strength_reps'
        })
    )
    
    agility_sec = forms.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[
            MinValueValidator(Decimal('5'), message='Must be between 5 and 60'),
            MaxValueValidator(Decimal('60'), message='Must be between 5 and 60')
        ],
        required=True,
        error_messages={
            'required': 'This field is required',
            'invalid': 'Must be a valid number',
        },
        widget=forms.TextInput(attrs={
            'class': 'form-control form-input',
            'placeholder': 'Enter value...',
            'name': 'agility_sec'
        })
    )
    
    speed_sec = forms.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[
            MinValueValidator(Decimal('4'), message='Must be between 4 and 20'),
            MaxValueValidator(Decimal('20'), message='Must be between 4 and 20')
        ],
        required=True,
        error_messages={
            'required': 'This field is required',
            'invalid': 'Must be a valid number',
        },
        widget=forms.TextInput(attrs={
            'class': 'form-control form-input',
            'placeholder': 'Enter value...',
            'name': 'speed_sec'
        })
    )
    
    endurance_time = forms.CharField(
        max_length=10,
        required=True,
        error_messages={
            'required': 'This field is required',
        },
        widget=forms.TextInput(attrs={
            'class': 'form-control form-input',
            'placeholder': 'mm:ss (e.g., 12:30)',
            'name': 'endurance_time'
        })
    )
    
    def clean_endurance_time(self):
        """Validate endurance time format and range (mm:ss, 4:00-30:00)."""
        time_str = self.cleaned_data.get('endurance_time', '').strip()
        
        if not time_str:
            raise ValidationError('This field is required')
        
        # Validate format
        time_pattern = re.compile(r'^(\d{1,2}):(\d{2})$')
        match = time_pattern.match(time_str)
        
        if not match:
            raise ValidationError('Format must be mm:ss (e.g., 12:30)')
        
        minutes = int(match.group(1))
        seconds = int(match.group(2))
        
        # Validate minutes range
        if minutes < 0 or minutes > 99:
            raise ValidationError('Minutes must be between 0-99')
        
        # Validate seconds range
        if seconds < 0 or seconds > 59:
            raise ValidationError('Seconds must be between 00-59')
        
        # Validate total time range (4:00 to 30:00)
        total_seconds = minutes * 60 + seconds
        if total_seconds < 240 or total_seconds > 1800:
            raise ValidationError('Time must be between 4:00 and 30:00')
        
        return time_str
    
    def clean_height_cm(self):
        """Ensure height is positive."""
        height = self.cleaned_data.get('height_cm')
        if height and height < 0:
            raise ValidationError('Must be a positive number')
        return height
    
    def clean_weight_kg(self):
        """Ensure weight is positive."""
        weight = self.cleaned_data.get('weight_kg')
        if weight and weight < 0:
            raise ValidationError('Must be a positive number')
        return weight
    
    def clean_vo2_distance_m(self):
        """Ensure distance is positive."""
        distance = self.cleaned_data.get('vo2_distance_m')
        if distance and distance < 0:
            raise ValidationError('Must be a positive number')
        return distance
    
    def clean_agility_sec(self):
        """Ensure agility time is positive."""
        agility = self.cleaned_data.get('agility_sec')
        if agility and agility < 0:
            raise ValidationError('Must be a positive number')
        return agility
    
    def clean_speed_sec(self):
        """Ensure speed time is positive."""
        speed = self.cleaned_data.get('speed_sec')
        if speed and speed < 0:
            raise ValidationError('Must be a positive number')
        return speed
