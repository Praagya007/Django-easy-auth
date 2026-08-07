from .views import RegisterInitialView
from django.urls import path

urlpatterns = [
    path("register/", RegisterInitialView.as_view(), name="register-initial"),
]