from django.contrib import admin
from .models import School, Student, AttendanceRecord, FlaggedEntry


@admin.register(School)
class SchoolAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'latitude', 'longitude', 'radius_meters')
    search_fields = ('name', 'id')
    ordering = ('id',)


class FlaggedEntryInline(admin.StackedInline):
    model = FlaggedEntry
    extra = 0
    can_delete = False
    readonly_fields = ('reviewed_at',)


@admin.register(AttendanceRecord)
class AttendanceRecordAdmin(admin.ModelAdmin):
    list_display = ('student', 'school', 'status', 'distance_meters', 'accuracy_meters', 'timestamp')
    list_filter = ('status', 'school', 'timestamp')
    search_fields = ('student__user__first_name', 'student__user__last_name', 'student__student_id')
    ordering = ('-timestamp',)
    inlines = [FlaggedEntryInline]


class AttendanceRecordInline(admin.TabularInline):
    model = AttendanceRecord
    extra = 0
    fields = ('school', 'status', 'distance_meters', 'timestamp')
    readonly_fields = ('timestamp',)
    show_change_link = True


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('get_full_name', 'student_id', 'school', 'user')
    list_filter = ('school',)
    search_fields = ('user__first_name', 'user__last_name', 'user__username', 'student_id')
    inlines = [AttendanceRecordInline]

    @admin.display(description='Full Name', ordering='user__first_name')
    def get_full_name(self, obj):
        return obj.user.get_full_name() or obj.user.username


@admin.register(FlaggedEntry)
class FlaggedEntryAdmin(admin.ModelAdmin):
    list_display = (
        'get_student',
        'flag_reason',
        'is_resolved',
        'approved',
        'get_timestamp',
        'reviewed_at'
    )
    list_filter = ('flag_reason', 'is_resolved', 'approved', 'attendance_record__timestamp')
    search_fields = (
        'attendance_record__student__user__first_name',
        'attendance_record__student__user__last_name',
        'attendance_record__student__student_id'
    )
    actions = ['approve_selected_entries']

    @admin.display(description='Student', ordering='attendance_record__student')
    def get_student(self, obj):
        return obj.attendance_record.student

    @admin.display(description='Timestamp', ordering='attendance_record__timestamp')
    def get_timestamp(self, obj):
        return obj.attendance_record.timestamp

    # Custom Admin Action to approve flagged entries in bulk from the dashboard
    @admin.action(description='Approve selected flagged entries')
    def approve_selected_entries(self, request, queryset):
        for entry in queryset:
            entry.is_resolved = True
            entry.approved = True
            entry.attendance_record.status = 'present'
            entry.attendance_record.save()
            entry.save()
        self.message_user(request, f"Successfully approved {queryset.count()} entry/entries.")