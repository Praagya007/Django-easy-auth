from allauth.account.adapter import DefaultAccountAdapter

class AccountAdapter(DefaultAccountAdapter):
    def save_user(self, request, user, form, commit=True):
        #1. Call super with commit=False to modify the model before it hits the db.
        user = super().save_user(request, user, form, commit=False)
        
        #2. Extract extra values validated by your HeadlessExtraSignupForm. These values are available in the form.cleaned_data dictionary.
        form_data = form.cleaned_data
        user.full_name = form_data.get('fullName', '') #Matches the frontend field.
        
        # Save to the db: 
        if commit:
            user.save()
            
        return user 
        
        