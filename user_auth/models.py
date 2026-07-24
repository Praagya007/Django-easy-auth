# AbstractUser and BaseUserManager to create a custom user model and manager.
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models


class UserManager(BaseUserManager):
    """
    Custom user manager to handle user creation with email as the unique identifier.
    """

    # Password= None, esp. essential if you have social logins, them users not need one.
    def create_user(self, email, full_name="", password=None, **extra_fields):

        if not email:
            raise ValueError("The Email field must be set")
        email = self.normalize_email(email)

        # Treats None and "" identically before calling strip. Small change, huge difference in behavior.
        full_name = (full_name or "").strip()

        user = self.model(email=email, full_name=full_name, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, full_name, password=None, **extra_fields):

        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")
        if extra_fields.get("is_active") is not True:
            raise ValueError("Superuser must have is_active=True.")

        return self.create_user(email, full_name, password, **extra_fields)


"""
Note: AbstractUser is better than AbstractBaseUser because it is fast, has built in permissions 
and is easier to implement. AbstractBaseUser requires a lot more work to implement, and 
has more chances of pitfalls. 
"""


class User(AbstractUser):
    # Remove the older legacy fields from the default User model
    username = None
    first_name = None
    last_name = None

    """
    Now, we add the fields that we actually need: 
    You don't need the required=True flag, because by default, all fields are required in Django models.
    """
    email = models.EmailField(unique=True)  # Make email unique, note unique auto creates an index

    # Note: We have altered full name to be optional, esp. because
    # Social logins may not guarantee a full name thing.
    # Avoid both null=True and blank=True, just a blank=True and default="" for CharField.
    # Note only set null=True when fields need to be unique. Nulls are not treated as duplicate entries.
    full_name = models.CharField(max_length=200, blank=True, default="")
    USERNAME_FIELD = "email"  # Set the email field as the unique identifier for authentication

    objects = UserManager()  # Use the custom user manager for creating users and superusers
    # This is required by the createsuperuser CLI utility. Not including this,
    # will throw errors when trying to create a superuser, due to Data Integrity requirements.
    # you might need to add: null=True, blank=True but to keep this universal, we will keep it as is.
    REQUIRED_FIELDS = ["full_name"]

    # Returns email.
    def __str__(self):
        return self.email

    # Returns full name.
    def get_full_name(self):
        return self.full_name

    """
    Note: The get_short_name method is used by Django's admin interface and other parts of the framework to display a user's short name. 
    In this case, we can return the first name from the full name, or if the full name is empty, 
    we can return the email as a fallback.
    """

    def get_short_name(self):
        # Safely extracts the first name, or falls back to the email if empty
        return self.full_name.split(" ")[0] if self.full_name else self.email
