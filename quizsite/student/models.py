from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()


class LearnerProfile(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    id_user = models.IntegerField()
    bio = models.TextField(blank=True)
    phone_num = models.TextField(blank=True, max_length=15)
    name = models.TextField(blank=True, max_length=100)
    dob = models.TextField(blank=True, max_length=20)
    gender = models.TextField(blank=True, max_length=10)
    rating = models.IntegerField(default=1000)

    def __str__(self):
        return self.user.username


class QuizRecord(models.Model):
    id_quiz = models.TextField(max_length=150)
    user = models.CharField(max_length=100)
    score = models.IntegerField()
    attempt_at = models.DateTimeField(default=timezone.now)
    rating_diff = models.IntegerField(default=None)
    correct = models.IntegerField(default=None)
    incorrect = models.IntegerField(default=None)
    total = models.IntegerField(default=None)
    time_taken = models.IntegerField(default=None)

    def __str__(self):
        return self.user


class RatingLog(models.Model):
    user = models.CharField(max_length=100)
    rating = models.IntegerField()
    affect_on = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.user
