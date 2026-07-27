from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login, name='login'),
    path('', views.checkin, name='checkin'),
    path('teacher-dashboard/', views.teacher_dashboard, name='teacher_dashboard'),
    path('api/checkin/', views.CheckInView.as_view(), name='api-checkin'),  
    path('logout/',views.logout_view,name='logout'),
    path('settings/', views.school_settings, name='school_settings'),
    path('settings/<int:school_id>/', views.school_settings, name='school_settings'),
    path('checkin/result/<int:record_id>/', views.checkin_result, name='checkin_result'),
]