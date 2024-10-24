from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('process-file/', views.process_file, name='process_file'),
    path('chat/', views.chat, name='chat'),
    path('upload-file/', views.upload_file, name='upload_file'),
]
