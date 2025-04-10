from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),  # Updated this line
    path('predict/', views.predict_api, name='predict_api'),
]
