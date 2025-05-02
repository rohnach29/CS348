from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from datetime import timedelta

class Runner(models.Model):
    """Model representing a runner user with additional information."""
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.TextField(blank=True, null=True)
    age = models.PositiveIntegerField(null=True, blank=True)
    height_cm = models.PositiveIntegerField(null=True, blank=True)
    weight_kg = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    profile_image = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}"

class Route(models.Model):
    """Model representing a running route."""
    name = models.CharField(max_length=100)
    creator = models.ForeignKey(Runner, on_delete=models.CASCADE, related_name='routes')
    start_location = models.CharField(max_length=255)
    end_location = models.CharField(max_length=255)
    distance_km = models.DecimalField(max_digits=6, decimal_places=2)
    elevation_gain_m = models.PositiveIntegerField(default=0)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.distance_km}km)"

class Run(models.Model):
    """Model representing a running activity."""
    runner = models.ForeignKey(Runner, on_delete=models.CASCADE, related_name='runs')
    route = models.ForeignKey(Route, on_delete=models.SET_NULL, null=True, blank=True, related_name='runs')
    title = models.CharField(max_length=100)
    date = models.DateField()
    start_time = models.TimeField()
    duration = models.DurationField(help_text="Duration in HH:MM:SS format")
    distance_km = models.DecimalField(max_digits=6, decimal_places=2)
    average_pace = models.DurationField(help_text="Average pace per km in MM:SS format", null=True, blank=True)
    calories_burned = models.PositiveIntegerField(null=True, blank=True)
    average_heart_rate = models.PositiveIntegerField(null=True, blank=True, 
                                                   validators=[MinValueValidator(30), MaxValueValidator(250)])
    notes = models.TextField(blank=True, null=True)
    weather_conditions = models.CharField(max_length=100, blank=True, null=True)
    temperature_c = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)
    is_public = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} - {self.date}"
    
    def save(self, *args, **kwargs):
        # Auto-calculate pace if not provided
        if not self.average_pace and self.duration and self.distance_km:
            total_seconds = self.duration.total_seconds()
            pace_seconds = total_seconds / float(self.distance_km)
            minutes = int(pace_seconds // 60)
            seconds = int(pace_seconds % 60)
            self.average_pace = timedelta(minutes=minutes, seconds=seconds)
        super().save(*args, **kwargs)

class Comment(models.Model):
    """Model representing comments on runs."""
    run = models.ForeignKey(Run, on_delete=models.CASCADE, related_name='comments')
    commenter = models.ForeignKey(Runner, on_delete=models.CASCADE, related_name='comments')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Comment by {self.commenter} on {self.run.title}"

class RunLike(models.Model):
    """Model representing likes on runs."""
    run = models.ForeignKey(Run, on_delete=models.CASCADE, related_name='likes')
    runner = models.ForeignKey(Runner, on_delete=models.CASCADE, related_name='liked_runs')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('run', 'runner')
        
    def __str__(self):
        return f"{self.runner} liked {self.run.title}"
