from django.contrib.auth.base_user import BaseUserManager, AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin
from django.db import models


class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        if password:
            user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields)


class CustomUser(AbstractBaseUser, PermissionsMixin):
    ROLE_CHOICES = [
        ('patient', 'Patient'),
        ('docteur', 'Docteur'),
    ]
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=15, null=True, blank=True)
    address = models.CharField(max_length=255, null=True, blank=True)
    role = models.CharField(max_length=50, choices=ROLE_CHOICES, default='patient')
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []
    objects = CustomUserManager()
    groups = models.ManyToManyField(
        'auth.Group',
        related_name='customuser_set',
        blank=True
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='customuser_set',
        blank=True
    )

    def __str__(self):
        return self.email
    def is_doctor(self):
        return self.role == 'docteur'

    def is_patient(self):
        return self.role == 'patient'


class Availability(models.Model):
    doctor = models.ForeignKey(CustomUser, limit_choices_to={'role': 'docteur'}, on_delete=models.CASCADE, related_name='availabilities')
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['doctor', 'start_time', 'end_time'], name='unique_availability')
        ]

    def __str__(self):
        return f"Disponibilité de Dr. {self.doctor.email} de {self.start_time} à {self.end_time}"


class Appointment(models.Model):
    doctor = models.ForeignKey(CustomUser, limit_choices_to={'role': 'docteur'}, on_delete=models.CASCADE, related_name='doctor_appointments')
    patient = models.ForeignKey(CustomUser, limit_choices_to={'role': 'patient'}, on_delete=models.CASCADE, related_name='patient_appointments')
    availability = models.ForeignKey(Availability, on_delete=models.CASCADE)
    symptoms = models.TextField(null=True, blank=True)
    status = models.CharField(max_length=50, choices=[('Pending', 'Pending'), ('Confirmed', 'Confirmed'), ('Completed', 'Completed')])

    def __str__(self):
        return f"Appointment with Dr. {self.doctor.email} for {self.patient.email} on {self.availability.start_time}"

class Treatment(models.Model):
    appointment = models.ForeignKey(Appointment, on_delete=models.CASCADE, related_name='treatments')
    medication_name = models.CharField(max_length=255)
    dosage_per_day = models.IntegerField()
    duration_in_days = models.IntegerField()
    notes = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"Treatment: {self.medication_name} for {self.appointment.patient.email} by Dr. {self.appointment.doctor.email}"


