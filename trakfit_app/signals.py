from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from .models import FitnessTest, Student, updates


@receiver(post_save, sender=Student)
def student_registered(sender, instance, created, **kwargs):
    """
    Signal to track when a student registers.
    """
    if created:
        student = instance
        full_name = f"{student.first_name} {student.last_name}"
        body = f"Student {full_name} registered"
        
        # Create an entry in the updates model
        updates.objects.create(student=student, body=body)


@receiver(post_save, sender=FitnessTest)
def update_student_timestamp(sender, instance, created, **kwargs):
    """
    Signal to update the student's updated_at field whenever a fitness test is created or updated.
    Also creates an entry in the updates model to track the change.
    """
    student = instance.student
    full_name = f"{student.first_name} {student.last_name}"
    
    # Determine the pronoun based on gender
    pronoun = "his/her"
    if student.gender:
        if student.gender.lower() in ['male', 'm']:
            pronoun = "his"
        elif student.gender.lower() in ['female', 'f']:
            pronoun = "her"
    
    # Update the student's last_data_update_at timestamp
    student.last_data_update_at = timezone.now()
    student.save(update_fields=['last_data_update_at', 'updated_at'])
    
    # Generate appropriate message based on action and test type
    if created:
        # New test created
        if instance.test_type == 'pre':
            body = f"{full_name} created {pronoun} pre-test"
        else:  # post test
            # Count existing post tests to get the number
            post_test_count = student.fitness_tests.filter(test_type='post').count()
            body = f"{full_name} created {pronoun} post test #{post_test_count}"
    else:
        # Test updated
        if instance.test_type == 'post':
            # Find which post test number this is
            post_tests = student.fitness_tests.filter(test_type='post').order_by('taken_at')
            test_number = 1
            for idx, test in enumerate(post_tests, start=1):
                if test.test_id == instance.test_id:
                    test_number = idx
                    break
            body = f"{full_name} updated {pronoun} post test #{test_number}"
        else:
            body = f"{full_name} updated {pronoun} pre-test"
    
    # Create an entry in the updates model to track this change
    updates.objects.create(student=student, body=body)
