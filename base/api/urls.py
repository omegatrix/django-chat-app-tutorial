from django.urls import path

from .views import get_routes, get_rooms, get_room

urlpatterns = [
    path('', get_routes),
    path('rooms/', get_rooms),
    path('rooms/<int:pk>/', get_room),
]
