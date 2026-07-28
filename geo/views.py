from math import radians, sin, cos, sqrt, atan2
from datetime import timedelta
from itertools import groupby

from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login, logout as django_logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.db.models import Count, Q
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status as http_status

from .models import School, AttendanceRecord, Student, FlaggedEntry
from .serializers import CheckInSerializer
from django_ratelimit.decorators import ratelimit


@ratelimit(key="ip", rate="60/m", block=True,method=['GET','POST'])
def haversine_distance(lat1, lon1, lat2, lon2):
    R = 6371000  # Earth's radius in meters
    phi1, phi2 = radians(lat1), radians(lat2)
    dphi = radians(lat2 - lat1)
    dlambda = radians(lon2 - lon1)

    a = sin(dphi / 2)**2 + cos(phi1) * cos(phi2) * sin(dlambda / 2)**2
    return 2 * R * atan2(sqrt(a), sqrt(1 - a))


@ratelimit(key="ip", rate="60/m", block=True,method=['GET','POST'])
def get_date_label(record_date):
    today = timezone.localdate()
    if record_date == today:
        return "Today"
    elif record_date == today - timedelta(days=1):
        return "Yesterday"
    else:
        return record_date.strftime("%A")  


@ratelimit(key="ip", rate="60/m", block=True,method=['GET','POST'])
def is_staff_user(user):
    return user.is_staff








class CheckInView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = CheckInSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            school = School.objects.get(id=data['school_id'])
        except School.DoesNotExist:
            return Response({'detail': 'School location not found.'}, status=http_status.HTTP_404_NOT_FOUND)

        student = getattr(request.user, 'student', None)
        if not student:
            return Response({'detail': 'No student profile linked to this account.'}, status=http_status.HTTP_403_FORBIDDEN)

        today = timezone.localdate()

       
        already_present = AttendanceRecord.objects.filter(
            student=student,
            school=school,
            timestamp__date=today,
            status__in=['present', 'flagged']
        ).exists()

        if already_present:
            return Response(
                {'detail': f'You have already checked in at {school.name} today!'},
                status=http_status.HTTP_400_BAD_REQUEST
            )

      
        distance = haversine_distance(
            data['latitude'], data['longitude'],
            school.latitude, school.longitude
        )

        if distance <= school.radius_meters:
            result_status = 'present'
        else:
         
            result_status = 'flagged'

        record = AttendanceRecord.objects.create(
            student=student,
            school=school,
            latitude=data['latitude'],
            longitude=data['longitude'],
            accuracy_meters=data.get('accuracy'),
            distance_meters=distance,
            status=result_status
        )

        if result_status == 'flagged':
            FlaggedEntry.objects.create(
                attendance_record=record,
                flag_reason='radius',
            )

        return Response({
            'status': record.status,
            'distance_meters': round(distance, 1),
            'timestamp': record.timestamp,
            'record_id': record.id,
        }, status=http_status.HTTP_201_CREATED)



@login_required
def checkin(request):
    student = getattr(request.user, 'student', None)
    if not student:
        messages.error(request, 'No student profile is linked to this account.')
        return redirect('login')

    today = timezone.localdate()

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

    return render(request, 'check_in.html', {
        'student': student,
        'schools_data': schools,
        'default_school_id': student.school_id,
        'checked_in_school_ids': checked_in_school_ids,
    })


@login_required
@ratelimit(key="ip", rate="60/m", block=True,method=['GET','POST'])
def attendance_history(request):
    student = getattr(request.user, 'student', None)
    if not student:
        messages.error(request, 'No student profile linked to this account.')
        return redirect('login')

    active_filter = request.GET.get('filter', 'week')
    queryset = AttendanceRecord.objects.filter(student=student).select_related('school').order_by('-timestamp')

    now = timezone.now()
    if active_filter == 'week':
        queryset = queryset.filter(timestamp__gte=now - timedelta(days=7))
    elif active_filter == 'month':
        queryset = queryset.filter(timestamp__gte=now - timedelta(days=30))

    total_records = queryset.count()
    present_count = queryset.filter(status='present').count()
    attendance_pct = round((present_count / total_records) * 100) if total_records > 0 else 0

    grouped_records = []
    for date, items in groupby(queryset, key=lambda r: r.timestamp.date()):
        grouped_records.append({
            'date': date,
            'date_label': get_date_label(date),
            'records': list(items)
        })

    return render(request, 'attendance_history.html', {
        'attendance_groups': grouped_records,
        'attendance_percentage': attendance_pct,
        'active_filter': active_filter,
        'current_streak': getattr(student, 'streak_count', 0),
    })


@login_required
@ratelimit(key="ip", rate="60/m", block=True,method=['GET','POST'])
def checkin_result(request, record_id):
    student = getattr(request.user, 'student', None)
    if not student:
        messages.error(request, 'No student profile linked to this account.')
        return redirect('login')

    record = get_object_or_404(AttendanceRecord, id=record_id, student=student)

    return render(request, 'checkin_result.html', {
        'record': record,
        'school': record.school,
    })


@ratelimit(key="ip", rate="60/m", block=True,method=['GET','POST'])
def login(request):
    if request.user.is_authenticated:
        return redirect('teacher_dashboard' if request.user.is_staff else 'checkin')

    if request.method == 'POST':
        identifier = request.POST.get('studentid')
        password = request.POST.get('password')
        usr = authenticate(request, username=identifier, password=password)

        if usr is not None:
            auth_login(request, usr)
            messages.success(request, 'Logged in successfully.')
            return redirect('teacher_dashboard' if usr.is_staff else 'checkin')
        else:
            messages.error(request, 'Invalid student ID or password.')

    return render(request, 'login.html')


def logout_view(request):
    django_logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('login')


@login_required
@user_passes_test(is_staff_user, login_url='login')
@ratelimit(key="ip", rate="60/m", block=True,method=['GET','POST'])
def teacher_dashboard(request):
    today = timezone.localdate()

    records_today = (
        AttendanceRecord.objects
        .filter(timestamp__date=today)
        .select_related('student', 'student__user', 'school')
        .order_by('-timestamp')
    )

    
    checked_in_student_ids = records_today.filter(
        status__in=['present', 'flagged']
    ).values_list('student_id', flat=True)

    not_checked_in = Student.objects.exclude(
        id__in=checked_in_student_ids
    ).select_related('user')

    total_expected = Student.objects.count()
    present_count = len(checked_in_student_ids)
    attendance_pct = round((present_count / total_expected) * 100) if total_expected > 0 else 0

    return render(request, 'teacher_dashboard.html', {
        'records': records_today,
        'not_checked_in': not_checked_in,
        'present_count': present_count,
        'expected_count': total_expected,
        'attendance_pct': attendance_pct,
    })

@login_required
@ratelimit(key="ip", rate="60/m", block=True,method=['GET','POST'])
def student_detail(request, student_id):
    student = get_object_or_404(Student, id=student_id)

    attendance_records = AttendanceRecord.objects.filter(
        student=student
    ).select_related('school').order_by('-timestamp')

    latest_record = attendance_records.first()

    today = timezone.now().date()
    start_date = today - timedelta(days=29)

    records_30_days = attendance_records.filter(
        timestamp__date__range=[start_date, today]
    )

    total_records = records_30_days.count()
    total_present = records_30_days.filter(status='present').count()
    total_flagged = records_30_days.filter(status='flagged').count()
    total_rejected = records_30_days.filter(status='rejected').count()

  
    if total_records > 0:
        attendance_percentage = round(((total_present + total_flagged) / total_records) * 100, 1)
    else:
        attendance_percentage = 100.0

    record_map = {
        rec.timestamp.date(): rec.status
        for rec in records_30_days
    }

    heatmap_days = []
    total_absences = 0
    current_date = start_date
    while current_date <= today:
        status = record_map.get(current_date, None)

        
        if not status and current_date.weekday() < 5: 
            if current_date < today:
                status = 'absent'
                total_absences += 1
            else:
                status = None

        heatmap_days.append({
            'date': current_date,
            'status': status,
            'is_padding': False
        })
        current_date += timedelta(days=1)

    context = {
        'student': student,
        'attendance_records': attendance_records[:10],
        'latest_record': latest_record,
        'attendance_percentage': attendance_percentage,
        'total_absences': total_absences,
        'total_flagged': total_flagged,
        'total_rejected': total_rejected,
        'heatmap_days': heatmap_days,
        'teacher': getattr(request.user, 'teacher_profile', None),
    }

    return render(request, 'student_detail.html', context)


@login_required
@user_passes_test(is_staff_user, login_url='login')
@ratelimit(key="ip", rate="60/m", block=True,method=['GET','POST'])
def school_settings(request, school_id=None):
    schools = School.objects.all()

    if school_id:
        school = get_object_or_404(School, id=school_id)
    else:
        school = schools.first()

    if request.method == 'POST':
        if school is None:
            messages.error(request, 'No school exists yet to configure.')
            return redirect('checkin')

        try:
            school.name = request.POST.get('name', school.name)
            school.latitude = float(request.POST.get('latitude'))
            school.longitude = float(request.POST.get('longitude'))
            school.radius_meters = int(request.POST.get('radius_meters'))
            school.save()
            messages.success(request, f'Configuration for {school.name} saved successfully.')
        except (TypeError, ValueError):
            messages.error(request, 'Invalid coordinates or radius submitted.')

        return redirect('school_settings_detail', school_id=school.id)

    return render(request, 'school_settings.html', {
        'school': school,
        'schools': schools,
    })


@login_required
@user_passes_test(is_staff_user, login_url='login')
@ratelimit(key="ip", rate="60/m", block=True,method=['GET','POST'])
def flagged_entries_view(request):
    flagged_entries = FlaggedEntry.objects.filter(
        is_resolved=False
    ).select_related('attendance_record__student__user', 'attendance_record__school')

    return render(request, 'flagged_entries.html', {'flagged_entries': flagged_entries})


@login_required
@user_passes_test(is_staff_user, login_url='login')
@ratelimit(key="ip", rate="60/m", block=True,method=['GET','POST'])
def approve_all_entries(request, entry_id):
    if request.method == "POST":
        entry = get_object_or_404(FlaggedEntry, id=entry_id)
        entry.is_resolved = True
        entry.approved = True
        entry.reviewed_at = timezone.now()

        entry.attendance_record.status = 'present'
        entry.attendance_record.save()
        entry.save()

    return redirect('flagged_entries')


@login_required
@user_passes_test(is_staff_user, login_url='login')
@ratelimit(key="ip", rate="60/m", block=True,method=['GET','POST'])
def approve_all_entries_view(request):
    if request.method == "POST":
        pending_entries = FlaggedEntry.objects.filter(is_resolved=False).select_related('attendance_record')
        now = timezone.now()

        for entry in pending_entries:
            entry.attendance_record.status = 'present'
            entry.attendance_record.save()

            entry.is_resolved = True
            entry.approved = True
            entry.reviewed_at = now
            entry.save()

    return redirect('flagged_entries')