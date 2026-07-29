from django.conf import settings
from django.db import models


class School(models.Model):
    id = models.PositiveIntegerField(primary_key=True)
    name = models.CharField(max_length=200)
    latitude = models.FloatField()
    longitude = models.FloatField()
    radius_meters = models.PositiveIntegerField(default=100)

    def __str__(self):
        return self.name


class Student(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    student_id = models.CharField(max_length=20, unique=True, null=True)
    school = models.ForeignKey(School, on_delete=models.CASCADE)
    streak_count = models.PositiveIntegerField(default=0)
    last_checkin_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} ({self.student_id})"


class AttendanceRecord(models.Model):
    STATUS_CHOICES = [
        ('present', 'Present'),
        ('rejected', 'Rejected'),
        ('flagged', 'Flagged'),
    ]

    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    school = models.ForeignKey(School, on_delete=models.CASCADE)
    latitude = models.FloatField()
    longitude = models.FloatField()
    accuracy_meters = models.FloatField(null=True, blank=True)
    distance_meters = models.FloatField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student} - {self.status.upper()} ({self.timestamp.strftime('%Y-%m-%d %H:%M')})"


class FlaggedEntry(models.Model):
    REASON_CHOICES = [
        ('radius', 'Out of Radius'),
        ('suspicious', 'Suspicious Activity / Spoofing'),
    ]

    # Link directly to the attendance attempt
    attendance_record = models.OneToOneField(
        AttendanceRecord, 
        on_delete=models.CASCADE, 
        related_name='flagged_detail'
    )
    
    flag_reason = models.CharField(max_length=20, choices=REASON_CHOICES, default='radius')
    
    
    device_info = models.CharField(max_length=100, default="Mobile Device (Verified)")
    integrity_status = models.CharField(max_length=100, blank=True, null=True, help_text="e.g., Low / Spoofing Alert")
    reported_location_name = models.CharField(max_length=100, blank=True, null=True, help_text="e.g., Library Wing")
    detected_velocity = models.CharField(max_length=50, blank=True, null=True, help_text="e.g., 120 km/h (Invalid)")

    is_resolved = models.BooleanField(default=False)
    approved = models.BooleanField(default=False)
    reviewed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-attendance_record__timestamp']
        verbose_name_plural = "Flagged Entries"

    def __str__(self):
        return f"Flagged: {self.attendance_record.student} - {self.get_flag_reason_display()}"