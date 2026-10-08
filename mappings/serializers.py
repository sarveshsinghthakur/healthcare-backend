from rest_framework import serializers

from doctors.serializers import DoctorSerializer
from .models import PatientDoctorMapping


class MappingSerializer(serializers.ModelSerializer):
    doctor_detail = DoctorSerializer(source='doctor', read_only=True)

    class Meta:
        model = PatientDoctorMapping
        fields = ('id', 'patient', 'doctor', 'doctor_detail', 'assigned_by', 'assigned_at')
        read_only_fields = ('id', 'assigned_by', 'assigned_at')

    def validate(self, attrs):
        request = self.context.get('request')
        patient = attrs.get('patient')
        doctor = attrs.get('doctor')
        if request and patient and patient.created_by_id != request.user.id:
            raise serializers.ValidationError('You can only assign doctors to your own patients.')
        if patient and doctor and PatientDoctorMapping.objects.filter(patient=patient, doctor=doctor).exists():
            raise serializers.ValidationError('This doctor is already assigned to this patient.')
        return attrs
