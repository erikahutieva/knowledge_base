from django.urls import path
from . import views
from .views import chat

urlpatterns = [
    path('main', views.discipline_list, name='home'),
    path('', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('discipline/<int:discipline_id>/', views.subject_list, name='subject_list'),
    path('subject/<int:subject_id>/teachers/', views.teacher_list, name='teacher_list'),
    path('teacher/<int:teacher_id>/', views.teacher_detail, name='teacher_detail'),
    path('teacher/<int:teacher_id>/upload/', views.upload_pdf, name='upload_pdf'),
    path('chat/', views.chat, name='chat'),
    path('ai-chat/', views.ai_chat, name='ai_chat'),
    path('api/chat/', views.chat_api, name='chat_api'),
]
