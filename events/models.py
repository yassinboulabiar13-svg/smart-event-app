from django.db import models
from django.contrib.auth.models import User

class Event(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    description = models.TextField()
    date = models.DateTimeField()
    location = models.CharField(max_length=200)
    guests_emails = models.TextField(help_text="Séparez les emails par des virgules")

    def __str__(self):
        return self.title

class Guest(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    email = models.EmailField()
    status = models.CharField(
        max_length=10,
        choices=[('Accepted', 'Accepted'), ('Declined', 'Declined'), ('Pending', 'Pending')],
        default='Pending'
    )

    def __str__(self):
        return f"{self.email} ({self.status})"
