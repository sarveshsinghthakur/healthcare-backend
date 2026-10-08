from django.db import IntegrityError, transaction
from rest_framework import generics, permissions, status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from doctors.serializers import DoctorSerializer
from patients.models import Patient
from .models import PatientDoctorMapping
from .serializers import MappingSerializer


def _patient_doctors_response(patient, mappings, request):
    """Standard response for 'doctors assigned to a patient' routes."""
    return Response({
        'patient_id': patient.id,
        'doctors': DoctorSerializer([m.doctor for m in mappings], many=True).data,
        'mappings': MappingSerializer(mappings, many=True, context={'request': request}).data,
    })


def _owned_patient(request, patient_id):
    return Patient.objects.filter(id=patient_id, created_by=request.user).first()


class MappingListCreateView(generics.ListCreateAPIView):
    serializer_class = MappingSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Each user sees mappings of their own patients only.
        return (
            PatientDoctorMapping.objects.select_related('patient', 'doctor', 'patient__created_by')
            .filter(patient__created_by=self.request.user)
        )

    def perform_create(self, serializer):
        try:
            # atomic: keeps the transaction usable if the DB constraint fires
            # on a concurrent duplicate request.
            with transaction.atomic():
                serializer.save(assigned_by=self.request.user)
        except IntegrityError:
            raise ValidationError('This doctor is already assigned to this patient.')


class PatientDoctorsView(APIView):
    """GET /api/mappings/patient/<patient_id>/ - doctors assigned to one of the user's patients."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, patient_id):
        patient = _owned_patient(request, patient_id)
        if patient is None:
            return Response({'error': 'Patient not found.'}, status=status.HTTP_404_NOT_FOUND)
        mappings = list(
            PatientDoctorMapping.objects.select_related('doctor').filter(patient=patient)
        )
        return _patient_doctors_response(patient, mappings, request)


class MappingDetailView(APIView):
    """GET/DELETE /api/mappings/<id>/ for the authenticated user's data.

    GET: if <id> matches one of the user's patient ids -> all doctors of that
    patient (spec route `GET /api/mappings/<patient_id>/`, empty list when the
    patient has no doctors); otherwise a single mapping by its id.
    Prefer /api/mappings/patient/<patient_id>/ for clarity.
    DELETE: removes a mapping by its mapping id (must belong to the user).
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        patient = _owned_patient(request, pk)
        if patient is not None:
            mappings = list(
                PatientDoctorMapping.objects.select_related('doctor').filter(patient=patient)
            )
            return _patient_doctors_response(patient, mappings, request)
        mapping = (
            PatientDoctorMapping.objects.select_related('doctor')
            .filter(id=pk, patient__created_by=request.user)
            .first()
        )
        if mapping:
            return Response(MappingSerializer(mapping, context={'request': request}).data)
        return Response(
            {'error': 'No mapping or patient found with this id.'},
            status=status.HTTP_404_NOT_FOUND,
        )

    def delete(self, request, pk):
        mapping = (
            PatientDoctorMapping.objects
            .filter(id=pk, patient__created_by=request.user)
            .first()
        )
        if not mapping:
            return Response({'error': 'Mapping not found.'}, status=status.HTTP_404_NOT_FOUND)
        mapping.delete()
        return Response({'message': 'Mapping deleted successfully.'})
