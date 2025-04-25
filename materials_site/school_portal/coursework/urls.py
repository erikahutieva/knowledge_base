from django.urls import path
from . import views
from .views import chat
from django.urls import path
from django.conf.urls import handler403, handler404, handler500
from .views import custom_error_view

handler403 = custom_error_view
handler404 = custom_error_view
handler500 = custom_error_view

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
