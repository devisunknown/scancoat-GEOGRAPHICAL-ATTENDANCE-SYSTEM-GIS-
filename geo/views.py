# views.py
from math import radians, sin, cos, sqrt, atan2
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status as http_status
from .models import School, AttendanceRecord, Student
from .serializers import CheckInSerializer
from django.contrib.auth import authenticate
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import login as auth_login
from django.contrib.auth import logout as django_logout
from django.contrib.auth.models import User
from django.utils import timezone


def haversine_distance(lat1, lon1, lat2, lon2):
    R = 6371000
    phi1, phi2 = radians(lat1), radians(lat2)
    dphi = radians(lat2 - lat1)
    dlambda = radians(lon2 - lon1)
    a = sin(dphi / 2)**2 + cos(phi1) * cos(phi2) * sin(dlambda / 2)**2
    return 2 * R * atan2(sqrt(a), sqrt(1 - a))


class CheckInView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = CheckInSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            school = School.objects.get(id=data['school_id'])
        except School.DoesNotExist:
            return Response({'detail': 'School not found'}, status=http_status.HTTP_404_NOT_FOUND)

        try:
            student = request.user.student
        except Student.DoesNotExist:
            return Response({'detail': 'No student profile linked to this account'}, status=http_status.HTTP_403_FORBIDDEN)

        today = timezone.localdate()

        # Check if already present AT THIS SPECIFIC SCHOOL today
        already_present_at_school = AttendanceRecord.objects.filter(
            student=student,
            school=school,
            timestamp__date=today,
            status='present'
        ).exists()

        if already_present_at_school:
            return Response(
                {'detail': f'You have already checked in at {school.name} today!'},
                status=http_status.HTTP_400_BAD_REQUEST
            )

        # Calculate distance
        distance = haversine_distance(
            data['latitude'], data['longitude'],
            school.latitude, school.longitude
        )
        result_status = 'present' if distance <= school.radius_meters else 'rejected'

        record = AttendanceRecord.objects.create(
            student=student,
            school=school,
            latitude=data['latitude'],
            longitude=data['longitude'],
            accuracy_meters=data.get('accuracy'),
            distance_meters=distance,
            status=result_status
        )

        return Response({
            'status': record.status,
            'distance_meters': round(distance, 1),
            'timestamp': record.timestamp,
            'record_id': record.id,
        }, status=http_status.HTTP_201_CREATED)


@login_required
def checkin(request):
    try:
        student = request.user.student
    except Student.DoesNotExist:
        messages.error(request, 'No student profile is linked to this account.')
        return redirect('login')

    today = timezone.localdate()

    # Pass list of school IDs where the student is ALREADY checked in today
    checked_in_school_ids = list(
        AttendanceRecord.objects.filter(
            student=student,
            timestamp__date=today,
            status='present'
        ).values_list('school_id', flat=True)
    )

    schools = list(
        School.objects.all().order_by('name').values(
            'id', 'name', 'latitude', 'longitude', 'radius_meters'
        )
    )

    return render(request, 'check in.html', {
        'student': student,
        'schools_data': schools,
        'default_school_id': student.school_id,
        'checked_in_school_ids': checked_in_school_ids,
    })
    
    

def login(request):
    if request.method == 'POST':
        identifier = request.POST.get('studentid')
        password = request.POST.get('password')
        usr = authenticate(request, username=identifier, password=password)

        if usr is not None:
            auth_login(request, usr)
            messages.success(request, 'Logged in successfully')

            if usr.is_staff:
                return redirect('teacher_dashboard')
            else:
                return redirect('checkin')
        else:
            messages.error(request, 'Invalid credentials')
            return render(request, 'login.html')

    return render(request, 'login.html')


@login_required
@user_passes_test(lambda u: u.is_staff, login_url='login')
def teacher_dashboard(request):
    today = timezone.localdate()

    records_today = (
        AttendanceRecord.objects
        .filter(timestamp__date=today)
        .select_related('student', 'student__user')
        .order_by('timestamp')
    )

    checked_in_ids = records_today.values_list('student_id', flat=True)
    not_checked_in = Student.objects.exclude(id__in=checked_in_ids).select_related('user')

    total_expected = Student.objects.count()
    present_count = records_today.filter(status='present').count()
    attendance_pct = round((present_count / total_expected) * 100) if total_expected else 0

    return render(request, 'teacher dashboard.html', {
        'records': records_today,
        'not_checked_in': not_checked_in,
        'present_count': present_count,
        'expected_count': total_expected,
        'attendance_pct': attendance_pct,
    })


def logout_view(request):
    django_logout(request)
    return redirect('login')


@login_required
@user_passes_test(lambda u: u.is_staff, login_url='login')
def school_settings(request, school_id=None):
    schools = School.objects.all()

    if school_id:
        school = get_object_or_404(School, id=school_id)
    else:
        school = schools.first()  # default to the first campus if none specified

    if request.method == 'POST':
        try:
            school.name = request.POST.get('name', school.name)
            school.latitude = float(request.POST.get('latitude'))
            school.longitude = float(request.POST.get('longitude'))
            school.radius_meters = int(request.POST.get('radius_meters'))
            school.save()
            messages.success(request, f'{school.name} configuration saved.')
        except (TypeError, ValueError):
            messages.error(request, 'Invalid coordinates or radius submitted.')
        return redirect('school_settings', school_id=school.id)

    return render(request, 'school_settings.html', {
        'school': school,
        'schools': schools,
    })


@login_required
def checkin_result(request, record_id):
    record = get_object_or_404(AttendanceRecord, id=record_id, student=request.user.student)
    return render(request, 'checkin_result.html', {
        'record': record,
        'school': record.school,
    })