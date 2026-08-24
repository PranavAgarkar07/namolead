from django.urls import path

from . import views

urlpatterns = [
    path("api/search/", views.search_posts, name="search_posts"),
    path("go/<slug:slug>/", views.go_redirect, name="go"),
    path("track/view/<slug:slug>/", views.pageview, name="pageview"),
    path("opportunities/", views.opportunities_list_view, name="opportunities"),
    path("about/", views.about_view, name="about"),
    path("team/", views.team_view, name="team"),
    path("events/", views.events_view, name="events"),
]