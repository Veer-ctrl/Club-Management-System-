# users/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    COURSE_CHOICES = [
        ('btech', 'B.Tech'),
        ('mtech', 'M.Tech'), 
        ('bca', 'BCA'),
        ('mca', 'MCA'),
        ('bba', 'BBA'),
        ('mba', 'MBA'),
        ('bsc', 'B.Sc'),
        ('msc', 'M.Sc'),
        ('other', 'Other'),
    ]
    
    YEAR_CHOICES = [
        ('1', 'First Year'),
        ('2', 'Second Year'),
        ('3', 'Third Year'),
        ('4', 'Fourth Year'),
        ('alumni', 'Alumni'),
    ]
    
    ROLE_CHOICES = (
        ('member', 'Member'),
        ('admin', 'Admin'),
        ('superadmin', 'Super Admin'),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='member')
    
    # Personal email for login (make it nullable first)
    personal_email = models.EmailField(
        unique=True, 
        verbose_name="Personal Email",
        blank=True,   # Allow blank initially
        null=True     # Allow null initially
    )
    
    # College email (optional, can be added later)
    college_email = models.EmailField(
        unique=True, 
        verbose_name="College Email ID",
        blank=True,
        null=True
    )
    
    # Academic details (optional, can be added later)
    course = models.CharField(max_length=20, choices=COURSE_CHOICES, blank=True)
    year = models.CharField(max_length=10, choices=YEAR_CHOICES, blank=True)
    branch = models.CharField(max_length=100, blank=True)
    enrollment_number = models.CharField(max_length=20, blank=True)
    
    # Contact info (optional)
    phone = models.CharField(max_length=15, blank=True)
    profile_picture = models.ImageField(upload_to='profiles/', blank=True)
    
    # Use personal_email as the username field for authentication
    USERNAME_FIELD = 'personal_email'
    REQUIRED_FIELDS = ['username']  # username is still required but not for login
    
    class Meta:
        swappable = 'AUTH_USER_MODEL'
    
    def __str__(self):
        return self.email