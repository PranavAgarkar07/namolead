from django.urls import path

from . import views

urlpatterns = [
    path("go/<slug:slug>/", views.go_redirect, name="go"),
    path("unlock/<slug:slug>/", views.unlock, name="unlock"),
    path("verify/<str:token>/", views.verify, name="verify"),
    path("track/view/<slug:slug>/", views.pageview, name="pageview"),
]
