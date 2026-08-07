from rest_framework import serializers
from django.contrib.auth import get_user_model

from .validators import DISPOSABLE_EMAIL_DOMAINS, email_regex_validator

        
        
User= get_user_model()

class InitialRegisterSerializer(serializers.ModelSerializer):
    """
    required=True is the default, but explicitly setting it guarantees it must exist.
    Plus, EmailField automatically validates the email format.
    """
    
    email = serializers.EmailField(required=True, validators=[email_regex_validator])
    # allow_blank=True and required=False make it optional
    full_name = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = User
        fields = ['email', 'full_name']


    """ The disposable_email_domains_blocklist.txt file is loaded in validators.py, so we can use it here.
    It is a list of disposable email domains, provided by Vegastack that is updated on a daily basis
    """
    def validate_email(self, value):
        # Check if the email domain is disposable
        domain = value.split('@')[-1]
        if domain in DISPOSABLE_EMAIL_DOMAINS:
            raise serializers.ValidationError("Disposable email addresses are not allowed.")
        return value
    
    
    def validate_full_name(self, value):
        # If the user provided a name, check its length. 
        if value and len(value.strip()) < 10:
            raise serializers.ValidationError("Full name must be at least 10 characters long.")
        return value

        
   
        
        
        