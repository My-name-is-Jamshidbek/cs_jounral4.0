from django.urls import path

from about.views import about

urlpatterns = [
    path('<int:pk>/', about, name='about'),
]