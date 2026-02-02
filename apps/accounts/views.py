from rest_framework import generics, status
from rest_framework.permissions import AllowAny
from .serializers import RegisterSerializer
from .services import register_user
from core.responses import success_response, error_response

# ------------------------ VIEWS --------------------

# ----------- View 1: API view to register a new user
class RegisterView(generics.GenericAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]

    # Override the post method
    def post(self, request, *args, **kwargs):
        # 1. Validation using the serializer
        serializer = self.get_serializer(data=request.data)
        
        # If there is a invalid field tghat the serializer detects
        if not serializer.is_valid():
            return error_response(
                message="Validation failed",
                errors=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Pass the data to the service which will handle the creation
            user = register_user(
                email=serializer.validated_data['email'],
                username=serializer.validated_data['username'],
                password=serializer.validated_data['password']
            )

            # Success Response
            return success_response(
                data=RegisterSerializer(user).data,
                message="User registered successfully!",
                status_code=status.HTTP_201_CREATED
            )

        except Exception as e:
            return error_response(
                message="An error occurred during registration",
                errors={"server": str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )