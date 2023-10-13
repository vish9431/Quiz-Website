import uuid
from datetime import datetime

from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class InstructorProfile(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    id_user = models.IntegerField()
    bio = models.TextField(blank=True)
    phone_num = models.TextField(blank=True, max_length=15)
    name = models.TextField(blank=True, max_length=100)
    dob = models.TextField(blank=True, max_length=20)
    gender = models.TextField(blank=True, max_length=10)

    def __str__(self):
        return self.user.username


class QuizPost(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    user = models.CharField(max_length=100)
    number = models.IntegerField()
    time_allot = models.IntegerField()
    tags = models.CharField(max_length=150)
    created_at = models.DateTimeField(default=datetime.now)
    title = models.TextField(max_length=100)
    total_marks = models.IntegerField(default=100)
    attempt_count = models.IntegerField(default=0)
    difficulty = models.TextField(default='easy')
    live = models.BooleanField(default=False)
    description = models.TextField(default=None)

    def __str__(self):
        return self.user


class LiveTime(models.Model):
    id = models.CharField(primary_key=True, max_length=100)
    start_time = models.DateTimeField(default=None)
    close_time = models.DateTimeField(default=None)

    def __str__(self):
        return self.id


class ContactRecord(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    name = models.CharField(max_length=100)
    email = models.CharField(max_length=100)
    subject = models.CharField(max_length=100)
    message = models.TextField()

    def __str__(self):
        return self.message
