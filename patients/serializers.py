from rest_framework import serializers

from config.validators import validate_phone
from .models import Patient


class PatientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Patient
        fields = ('id', 'name', 'age', 'gender', 'address', 'phone', 'disease', 'created_by', 'created_at', 'updated_at')
        read_only_fields = ('id', 'created_by', 'created_at', 'updated_at')

    def validate_name(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError('Name is required.')
        return value

    def validate_age(self, value):
        if not 1 <= value <= 150:
            raise serializers.ValidationError('Age must be between 1 and 150.')
        return value

    def validate_phone(self, value):
        return validate_phone(value)
