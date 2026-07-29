# scancoat-GEOGRAPHICAL-ATTENDANCE-SYSTEM-GIS-
this is an early preview

# 📍 Scancoat GIS Attendance

**Scancoat GIS Attendance** is an intelligent, location-aware attendance verification system built with **Django** and **Tailwind CSS**. Designed to streamline physical attendance tracking using Geographic Information Systems (GIS) logic, it verifies check-ins against real-time campus geofencing and automatically flags out-of-radius or suspicious attempts for admin review.

---

## ✨ Key Features

* 🗺️ **GIS Geofenced Check-Ins**: Validates student coordinates (`latitude`, `longitude`) against predefined perimeter limits (`allowed_perimeter`) to calculate distance accurately.
* ⚠️ **Automated Anomaly Detection**: Automatically flags check-ins failing radius requirements (`flag_reason = 'radius'`) or suspicious device activity for teacher verification.
* 👨‍🏫 **Instructor Audit Console**:
  * Live **Flagged Entries Panel** to review pending or rejected check-in records.
  * One-click individual or batch approvals (`approve_entry` / `approve_all_entries`).
  * Integrated Google Maps Static API preview for location verification.
  * Direct contact options to follow up with flagged students.
* 📱 **Device & Profile Tracking**: Captures device signatures and distance metrics (`distance`) alongside student avatars for quick identification.

---

## 🛠️ Tech Stack

* **Backend**: Python 3.12+, Django 5.x
* **Frontend**: Django Templates, Tailwind CSS, Material Symbols Icons
* **GIS / Mapping**: Google Static Maps API, Haversine/Proximity Distance Metrics
* **Database**: SQLite (Development) / PostgreSQL (Production)

---

## 📁 Project Structure

```text
scancoat-gis-attendance/
├── attendance/              # Core application logic
│   ├── models.py            # AttendanceRecord, FlaggedEntry models
│   ├── views.py             # Dashboard, Flagged Entries review, Approval logic
│   ├── urls.py              # URL routes (approve_entry, contact_student, etc.)
│   └── admin.py             # Admin panel setup
├── templates/               # HTML templates
│   ├── flagged_entries.html # Complete flagged entries dashboard UI
│   └── ...                  # Base & authentication templates
├── static/                  # Static assets (CSS, JS, Images)
├── manage.py                # Django CLI tool
└── README.md                # Project documentation
