from django.db import models
from django.conf import settings

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
    entry_fee = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    PAYMENT_CHOICES = [
        ('online', 'Online Payment'),
        ('onsite', 'Pay at Event'),
    ]
    payment_option = models.CharField(max_length=10, choices=PAYMENT_CHOICES, default='online')
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
    is_paid = models.BooleanField(default=False)
    amount_paid = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    payment_method = models.CharField(max_length=30, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        unique_together = ['event', 'user']
    
    def __str__(self):
        return f"{self.user} - {self.event}"


class EventMedia(models.Model):
    MEDIA_TYPES = [
        ('photo', 'Photo'),
        ('video', 'Video'),
    ]

    media_type = models.CharField(max_length=10, choices=MEDIA_TYPES)
    file = models.FileField(upload_to='event_media/')
    title = models.CharField(max_length=200, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    event = models.ForeignKey('Event', on_delete=models.CASCADE, related_name='media_items')
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    class Meta:
        ordering = ['-uploaded_at']

    def __str__(self):
        if self.title:
            return self.title
        return f"{self.media_type} - {self.event.title}"


class EventFeedback(models.Model):
    event = models.ForeignKey('Event', on_delete=models.CASCADE, related_name='feedbacks')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='event_feedbacks')
    rating = models.IntegerField(choices=[(1, '1 Star'), (2, '2 Stars'), (3, '3 Stars'), (4, '4 Stars'), (5, '5 Stars')])
    comment = models.TextField(blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['event', 'user']
        ordering = ['-submitted_at']

    def __str__(self):
        return f"{self.user} - {self.event.title} - {self.rating} Stars"