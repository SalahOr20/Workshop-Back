from django.contrib.auth import authenticate
from django.contrib.auth.hashers import make_password
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from .models import Appointment, CustomUser
from .serializer import UserSerializer, AppointmentSerializer, PatientProfileSerializer, TreatmentSerializer


@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    if request.method == 'POST':
        data = request.data.copy()
        password = data.get('password')

        # Vérifier si le mot de passe est fourni
        if not password:
            return Response({'error': 'Password is required'}, status=status.HTTP_400_BAD_REQUEST)

        # Hacher le mot de passe avant de le sauvegarder
        hashed_password = make_password(password)
        data['password'] = hashed_password

        user_serializer = UserSerializer(data=data)

        if user_serializer.is_valid():
            user = user_serializer.save()

            role = data.get('role')
            if role == 'docteur':
                user.role = 'docteur'
                user.save()

            elif role == 'patient':
                user.role = 'patient'
                user.save()

            return Response({
                'message': 'User registered successfully'
            }, status=status.HTTP_201_CREATED)

        return Response(user_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    email = request.data.get('email')
    password = request.data.get('password')
    user = authenticate(email=email, password=password)

    if user:
        refresh = RefreshToken.for_user(user)
        response_data = {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }
        return Response(response_data, status=status.HTTP_200_OK)

    return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)


@api_view(['GET', 'PUT'])
@permission_classes([IsAuthenticated])
def patient_profile(request):
    patient = request.user

    if request.method == 'GET':
        serializer = PatientProfileSerializer(patient)
        return Response(serializer.data)

    elif request.method == 'PUT':
        serializer = PatientProfileSerializer(patient, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def book_appointment(request):
    data = request.data.copy()
    data['patient'] = request.user.id

    appointment_serializer = AppointmentSerializer(data=data)

    if appointment_serializer.is_valid():
        appointment = appointment_serializer.save()
        return Response({'message': 'Rendez-vous réservé avec succès', 'appointment_id': appointment.id},
                        status=status.HTTP_201_CREATED)

    return Response(appointment_serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_treatments(request, appointment_id):
    appointment = Appointment.objects.filter(id=appointment_id).first()

    if not appointment:
        return Response({'error': 'Appointment not found.'}, status=status.HTTP_404_NOT_FOUND)
    if appointment.doctor != request.user:
        return Response({'error': 'You do not have permission to add treatments to this appointment.'},
                        status=status.HTTP_403_FORBIDDEN)

    treatments_data = request.data.get('treatments', [])

    if not treatments_data:
        return Response({'error': 'No treatments provided.'}, status=status.HTTP_400_BAD_REQUEST)

    for treatment_data in treatments_data:
        treatment_serializer = TreatmentSerializer(data=treatment_data)
        if treatment_serializer.is_valid():
            treatment_serializer.save(appointment=appointment)
        else:
            return Response(treatment_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    return Response({'message': 'Treatments added successfully.'}, status=status.HTTP_201_CREATED)

@api_view(['GET', 'PUT'])
@permission_classes([IsAuthenticated])
def doctor_profile(request):
    user = request.user

    if request.method == 'GET':
        serializer = UserSerializer(user)
        return Response(serializer.data)

    elif request.method == 'PUT':
        serializer = UserSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def validate_appointment(request, appointment_id):
    appointment = Appointment.objects.filter(id=appointment_id).first()

    if not appointment:
        return Response({'error': 'Appointment not found.'}, status=status.HTTP_404_NOT_FOUND)
    if appointment.doctor != request.user:
        return Response({'error': 'You do not have permission to validate this appointment.'}, status=status.HTTP_403_FORBIDDEN)

    appointment.status = 'Confirmed'
    appointment.save()
    return Response({'message': 'Appointment validated successfully.'}, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def patient_info(request, appointment_id):
    # Retrieve the appointment using the appointment_id
    appointment = Appointment.objects.filter(id=appointment_id).first()

    # Check if the appointment exists
    if not appointment:
        return Response({'error': 'Appointment not found.'}, status=status.HTTP_404_NOT_FOUND)

    # Fetch the patient associated with the appointment
    patient = appointment.patient

    # Ensure the patient is of the correct role (optional, since the appointment links to a patient)
    if not patient or patient.role != 'patient':
        return Response({'error': 'Patient not found or invalid role.'}, status=status.HTTP_404_NOT_FOUND)

    # Serialize the patient information
    serializer = UserSerializer(patient)

    # Prepare the response data to include patient info and symptoms
    response_data = {
        'patient_info': serializer.data,
        'symptoms': appointment.symptoms,  # Add symptoms from the appointment
    }

    # Return the response data
    return Response(response_data, status=status.HTTP_200_OK)



@api_view(['GET'])
@permission_classes([IsAuthenticated])
def patient_treatments(request):
    user = request.user
    appointments = Appointment.objects.filter(patient=user)

    treatments_data = []

    for appointment in appointments:
        treatments = appointment.treatments.all()
        for treatment in treatments:
            treatments_data.append({
                'appointment_id': appointment.id,
                'treatment_name': treatment.name,
                'duration': treatment.duration,
                'frequency': treatment.frequency,
                'notes': treatment.notes,
            })

    return Response(treatments_data, status=status.HTTP_200_OK)