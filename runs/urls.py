from django.urls import path
from . import views

app_name = 'runs'

urlpatterns = [
    # Runner profile
    path('register/', views.register, name='register'),
    path('create-runner/', views.create_runner, name='create_runner'),
    
    # Run CRUD operations (Requirement 1)
    path('', views.run_list, name='run_list'),
    path('runs/create/', views.create_run, name='create_run'),
    path('runs/<int:pk>/', views.run_detail, name='run_detail'),
    path('runs/<int:pk>/edit/', views.update_run, name='update_run'),
    path('runs/<int:pk>/delete/', views.delete_run, name='delete_run'),
    
    # Route operations
    path('routes/', views.route_list, name='route_list'),
    path('routes/create/', views.create_route, name='create_route'),
    
    # Report interface (Requirement 2)
    path('reports/', views.run_report, name='run_report'),
    
    # Social features
    path('runs/<int:run_id>/comment/', views.add_comment, name='add_comment'),
    path('runs/<int:run_id>/toggle-like/', views.toggle_like, name='toggle_like'),
    
    # Public runs
    path('public-runs/', views.public_runs, name='public_runs'),
    path('user/<str:username>/runs/', views.view_user_runs, name='view_user_runs'),
] 