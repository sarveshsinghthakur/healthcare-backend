from rest_framework import serializers

from config.validators import normalize_email, validate_phone
from .models import Doctor


class DoctorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Doctor
        fields = ('id', 'name', 'specialization', 'phone', 'email', 'created_at', 'updated_at')
        read_only_fields = ('id', 'created_at', 'updated_at')

    def validate_name(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError('Name is required.')
        return value

    def validate_specialization(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError('Specialization is required.')
        return value

    def validate_phone(self, value):
        return validate_phone(value)

    def validate_email(self, value):
        return normalize_email(value)
