from django.urls import path

from .views import login_view, register, patient_profile, book_appointment, add_treatments, doctor_profile, \
    validate_appointment, patient_info

urlpatterns = [
    path('register/', register, name='user-register'),
    path('login/', login_view, name='login_view'),
    path('profile/', patient_profile, name='patient_profile'),
    path('book-appointment/', book_appointment, name='book_appointment'),
    path('add-treatments/<int:appointment_id>/', add_treatments, name='add_treatments'),
    path('doctor/profile/', doctor_profile, name='doctor_profile'),
    path('appointments/validate/<int:appointment_id>/', validate_appointment, name='validate_appointment'),
    path('patient/<int:patient_id>/', patient_info, name='patient_info'),
]
