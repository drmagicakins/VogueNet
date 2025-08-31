from django.urls import path
from .views import InitiateOrderView, VerifyOrderView

urlpatterns = [
    path("initiate/", InitiateOrderView.as_view(), name="orders_initiate"),
    path("verify/",   VerifyOrderView.as_view(),   name="orders_verify"),
]
