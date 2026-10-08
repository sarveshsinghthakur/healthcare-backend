from django.conf import settings
from django.db import models


class PatientDoctorMapping(models.Model):
    patient = models.ForeignKey('patients.Patient', on_delete=models.CASCADE, related_name='doctor_mappings')
    doctor = models.ForeignKey('doctors.Doctor', on_delete=models.CASCADE, related_name='patient_mappings')
    assigned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='mappings'
    )
    assigned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-assigned_at']
        constraints = [
            models.UniqueConstraint(fields=('patient', 'doctor'), name='uniq_patient_doctor'),
        ]

    def __str__(self):
        return f'Patient {self.patient_id} -> Doctor {self.doctor_id}'
