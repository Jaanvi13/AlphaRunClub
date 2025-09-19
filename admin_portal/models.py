from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class Event(models.Model):
    STATUS_CHOICES = [
        ('upcoming', 'Upcoming'),
        ('past', 'Past'),
        ('cancelled', 'Cancelled'),
        ('draft', 'Draft'),
    ]

    EVENT_TYPE_CHOICES = [
        ('networking_run', 'Networking Run'),
        ('coffee_rave_run', 'Coffee Rave Run'),
        ('bootcamp', 'BootCamp'),
        ('community_event', 'Community Event'),
        ('others', 'Others'),
    ]

    title = models.CharField(max_length=50)
    description = models.TextField()

    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField(null=True, blank=True)

    location = models.CharField(max_length=255)
    cover_image = models.ImageField(upload_to='image/', blank=True, null=True)

    organizer_name = models.CharField(max_length=255, default="Alpha Run Club")
    contact_email = models.EmailField(default="alpharunclub@gmail.com", null=True)
    contact_phone = models.CharField(max_length=15, default="9403253509", null=True)

    event_type = models.CharField(max_length=50, choices=EVENT_TYPE_CHOICES, default='networking_run')
    tags = models.CharField(max_length=255, blank=True, help_text="Comma-separated tags")

    registration_required = models.BooleanField(default=True)
    registration_link = models.URLField(blank=True, null=True)
    capacity = models.PositiveIntegerField(null=True, blank=True)
    price = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)

    cta_text = models.CharField(max_length=50, default="Register Now")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='upcoming')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    gallery = models.URLField(blank=True, null=True, help_text="Link to Google Photos")

    def __str__(self):
        return self.title


class Payment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    event = models.ForeignKey(Event, on_delete=models.CASCADE, blank=True, null=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)
    status = models.CharField(max_length=20, default="PENDING")  # SUCCESS / FAILED
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.event} - {self.status}"

    @property
    def total_amount(self):
        return self.amount * self.quantity


class PlanPayment(models.Model):
    STATUS_CHOICES = [
        ('SUCCESS', 'Success'),
        ('PENDING', 'Pending'),
        ('FAILED', 'Failed'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    plan_type = models.CharField(max_length=50)  # monthly, quarterly, half-yearly
    amount = models.FloatField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)
    razorpay_order_id = models.CharField(max_length=100, blank=True, null=True)
    payment_id = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.plan_type} - {self.status}"