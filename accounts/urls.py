from django.urls import path
from . import views
from .views import RegisterView, LoginView, ProfileView


urlpatterns = [
    path("api/register/", RegisterView.as_view(), name="register"),
    path("api/login/", LoginView.as_view(), name="login"),
    path("api/me/", ProfileView.as_view(), name="profile"),
]


