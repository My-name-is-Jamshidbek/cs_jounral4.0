from django.urls import path
from . import views

urlpatterns = [
    path('current/', views.current_issue, name='current_issue'),
    path('<int:pk>/', views.item_issue, name='item_issue'),
    path('all/', views.all_issues, name='all_issues'),
]
