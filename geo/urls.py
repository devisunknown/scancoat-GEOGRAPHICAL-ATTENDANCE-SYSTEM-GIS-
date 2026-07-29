from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('api/check-in/', views.CheckInView.as_view(), name='api_checkin'),
    path('', views.checkin, name='checkin'),
    path('history/', views.attendance_history, name='history'),
    path('checkin/result/<int:record_id>/', views.checkin_result, name='checkin_result'),
    path('teacher/', views.teacher_dashboard, name='teacher_dashboard'),
    path('student/student_detail/<int:student_id>/', views.student_detail, name='student_detail'),
    path('teacher/settings/', views.school_settings, name='school_settings'),
    path('teacher/settings/<int:school_id>/', views.school_settings, name='school_settings_detail'),
    path('teacher/flagged/', views.flagged_entries_view, name='flagged_entries'),
    path('teacher/flagged/<int:entry_id>/approve/', views.approve_all_entries, name='approve_all_entries'),
    path('teacher/flagged/approve-all/', views.approve_all_entries_view, name='approve_all_entries_view'),
    path('student/teacher/privacy policy',views.policy,name='privacy')
]