from django.db import models

class Event(models.Model):
    EVENT_TYPES = [
        ('workshop', 'Workshop'),
        ('seminar', 'Seminar'),
        ('competition', 'Competition'),
        ('social', 'Social Event'),
        ('meeting', 'General Meeting'),
    ]
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('upcoming', 'Upcoming'),
        ('ongoing', 'Ongoing'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    created_at = models.DateTimeField(auto_now_add=True)
    
    title = models.CharField(max_length=200)
    description = models.TextField()
    event_type = models.CharField(max_length=20, choices=EVENT_TYPES)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    location = models.CharField(max_length=200)
    capacity = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    club = models.ForeignKey('clubs.Club', on_delete=models.CASCADE)
    created_by = models.ForeignKey('users.CustomUser', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='events/', blank=True)
    is_public = models.BooleanField(default=True)
    
    def __str__(self):
        return self.title

class Registration(models.Model):
    STATUS_CHOICES = [
        ('registered', 'Registered'),
        ('attended', 'Attended'),
        ('cancelled', 'Cancelled'),
        ('waiting', 'Waiting List'),
    ]
    
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    user = models.ForeignKey('users.CustomUser', on_delete=models.CASCADE)
    registered_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='registered')
    
    class Meta:
        unique_together = ['event', 'user']
    
    def __str__(self):
        return f"{self.user} - {self.event}"