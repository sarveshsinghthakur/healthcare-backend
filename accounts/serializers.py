from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.db import IntegrityError, transaction
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken

from config.validators import normalize_email

User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True, required=True, max_length=128, validators=[validate_password]
    )

    class Meta:
        model = User
        fields = ('id', 'name', 'email', 'password')

    def validate_name(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError('Name is required.')
        return value

    def validate_email(self, value):
        email = normalize_email(value)
        if User.objects.filter(email=email).exists():
            raise serializers.ValidationError('A user with this email already exists.')
        return email

    def create(self, validated_data):
        email = validated_data['email']
        try:
            # atomic block keeps the transaction usable if IntegrityError fires
            # (e.g. a concurrent request registered the same email first).
            with transaction.atomic():
                user = User(username=email, email=email, name=validated_data['name'])
                user.set_password(validated_data['password'])
                user.save()
        except IntegrityError:
            raise serializers.ValidationError({'email': 'A user with this email already exists.'})
        return user


class LoginSerializer(serializers.Serializer):
    """Login with 'email' + 'password', returns a JWT access/refresh pair."""

    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True, write_only=True, max_length=128)

    def validate(self, attrs):
        email = normalize_email(attrs['email'])
        password = attrs['password']
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            # Run the hasher once to keep timing consistent with the valid-user path.
            User().set_password(password)
            raise serializers.ValidationError('Invalid email or password.', code='authorization')
        if not user.check_password(password) or not user.is_active:
            raise serializers.ValidationError('Invalid email or password.', code='authorization')
        refresh = RefreshToken.for_user(user)
        return {'refresh': str(refresh), 'access': str(refresh.access_token)}
