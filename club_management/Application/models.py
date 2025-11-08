from django.db import models
from users.models import CustomUser
from clubs.models import Club
class Application(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('waiting_list', 'Waiting List'),
    ]
    
    user = models.ForeignKey('users.CustomUser', on_delete=models.CASCADE)
    club = models.ForeignKey('clubs.Club', on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    applied_date = models.DateTimeField(auto_now_add=True)
    reviewed_date = models.DateTimeField(null=True, blank=True)
    
    # Application questions
    why_join = models.TextField(verbose_name="Why do you want to join this club?")
    skills = models.TextField(verbose_name="What skills can you contribute?")
    experience = models.TextField(blank=True, verbose_name="Previous experience")
    expectations = models.TextField(verbose_name="What do you expect from the club?")
    
    # Review info
    reviewed_by = models.ForeignKey('users.CustomUser', related_name='reviewed_applications', 
                                  null=True, blank=True, on_delete=models.SET_NULL)
    notes = models.TextField(blank=True, verbose_name="Review Notes")
    
    class Meta:
        unique_together = ['user', 'club']
    
    def __str__(self):
        return f"{self.user} - {self.club} Application"