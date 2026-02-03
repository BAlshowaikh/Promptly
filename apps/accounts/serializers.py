from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()

# --------- Serializer 1: Handle registring the user
class RegisterSerializer(serializers.ModelSerializer):
    # Validation for the password field
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'password')