from django.conf import settings
from django.db import models

class School(models.Model):
    id=models.PositiveIntegerField(primary_key=True)
    name = models.CharField(max_length=200)   
    latitude = models.FloatField()
    longitude = models.FloatField()
    radius_meters = models.PositiveIntegerField(default=100)


class Student(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    student_id = models.CharField(max_length=20, unique=True,null=True)
    school = models.ForeignKey(School, on_delete=models.CASCADE)

class AttendanceRecord(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    school = models.ForeignKey(School, on_delete=models.CASCADE)
    latitude = models.FloatField()
    longitude = models.FloatField()
    accuracy_meters = models.FloatField(null=True, blank=True)
    distance_meters = models.FloatField()
    status = models.CharField(max_length=10, choices=[('present', 'Present'), ('rejected', 'Rejected')])
    timestamp = models.DateTimeField(auto_now_add=True)