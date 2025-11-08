from django.db import models
# from clubs.models import Club

class Club(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField()
    logo = models.ImageField(upload_to='club_logos/', blank=True)
    founded_date = models.DateField(auto_now_add=True)
    contact_email = models.EmailField()
    website = models.URLField(blank=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return self.name

class Membership(models.Model):
    ROLE_CHOICES = [
        ('member', 'Member'),
        ('coordinator', 'Coordinator'),
        ('leader', 'Leader'),
        ('admin', 'Admin'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('alumni', 'Alumni'),
    ]
    
    user = models.ForeignKey('users.CustomUser', on_delete=models.CASCADE)
    club = models.ForeignKey(Club, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='member')
    join_date = models.DateField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    
    class Meta:
        unique_together = ['user', 'club']
        verbose_name_plural = "Memberships"
    
    def __str__(self):
        return f"{self.user} - {self.club} ({self.role})"