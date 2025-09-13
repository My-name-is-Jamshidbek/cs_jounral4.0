from django.urls import path

from submit import views

urlpatterns = [
    path('permissions/<int:pk>', views.permissions, name='permission'),
    path('submission/', views.submission, name='submission'),
    path('permission/', views.permission, name='demo_permission'),
]
