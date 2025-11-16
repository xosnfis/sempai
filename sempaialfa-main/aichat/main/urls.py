from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('cabinet/', views.cabinet, name='cabinet'),
    path('chat/', views.chat, name='chat'),
    path('api/chat/', views.chat_api, name='chat_api'),
    path('api/check-lm-studio/', views.check_lm_studio_connection, name='check_lm_studio'),
    path('api/user-data/', views.get_user_data, name='get_user_data'),
    path('api/create-event/', views.create_calendar_event, name='create_calendar_event'),
    path('transfer/', views.transfer, name='transfer'),
    path('receipts/', views.receipts, name='receipts'),
    path('utilities/', views.utilities, name='utilities'),
    path('taxes/', views.taxes, name='taxes'),
    path('calendar/', views.calendar, name='calendar'),
    path('documents/', views.documents, name='documents'),
    path('inventory/', views.inventory, name='inventory'),
    path('employees/', views.employees, name='employees'),
    path('support/', views.support, name='support'),
    path('mail/', views.mail, name='mail'),
    path('login/', views.login, name='login'),
    path('feedback/', views.feedback, name='feedback'),
]

