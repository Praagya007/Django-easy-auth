from django.shortcuts import render
from rest_framework.generics import CreateAPIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework import permissions
from .tasks import process_initial_registration

from user_auth.serializers import InitialRegisterSerializer
# Create your views here.


# Only accept POST requests.
class RegisterInitialView(CreateAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = InitialRegisterSerializer
    
    
    """
     Now, we override the create method to customize the response after a successful registration. 
     It will be on the initial phases, no password input for now.
     The password will be added once the email is verified.
     """
    def create(self, request, *args, **kwargs):
        # Pass input to the serializer.
        serializer = self.get_serializer(data=request.data)
        
        # Validate data (throws 400 bad request if invalid).
        serializer.is_valid(raise_exception=True)
        
        # Offload user registration and sending email to a queue (Celery) to avoid blocking the request.
        process_initial_registration.delay(serializer.validated_data)
        
        # Finally, return a generic response immediately, never leak whether the email is already registered or not.
        return Response(
            {"message": "If the email is not already registered,"
                " you will receive an email with an OTP to verify your email address."},
            status=status.HTTP_202_ACCEPTED
        )
        