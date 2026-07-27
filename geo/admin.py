# yourapp/admin.py
from django.contrib import admin
from .models import Student, School, AttendanceRecord

admin.site.register(Student)
admin.site.register(School)
admin.site.register(AttendanceRecord)