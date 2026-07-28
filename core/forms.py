from django import forms
import html

class HeadlessExtraSignupForm(forms.Form):
    """
    A form for collecting extra user information during signup.
    This form is used in conjunction with django-allauth's headless mode.
    """

    # Map this as fullName instead of full_name to match the frontend field name.
    fullName = forms.CharField(max_length=200, required= False) 
        
    def clean_fullName(self):
        """
        Cleans and sanitizes the fullName field.
        Automatically handles null bytes and escapes script structures.
        """
        data = self.cleaned_data.get('fullName', '')
        if data is None:
            return ''
            
        # 1. Remove null bytes completely
        cleaned_data = data.replace('\x00', '')
        
        # 2. Escape HTML characters to prevent XSS script injection
        sanitized_data = html.escape(cleaned_data)
        
        return sanitized_data.strip()
    
    
    def signup(self, request, user):
        """
        The adapter handles the data extraction and saving.
        We need this method because it is mandatory every time 
        you add a custom field in allauth.
        """
        pass