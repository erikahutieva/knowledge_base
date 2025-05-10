import os
from django.core.files.storage import FileSystemStorage
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseForbidden, JsonResponse
from .models import Discipline, Subject, Teacher, PDFFile
from .forms import PDFUploadForm
from django.conf import settings
import openai
from PIL import Image
import pytesseract
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q
from django.shortcuts import render
from .models import query_llama
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
import subprocess

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, 'Неверное имя пользователя или пароль')
    
    return render(request, 'login.html')

def logout_view(request):
    logout(request)
    return redirect('login')

@login_required
def discipline_list(request):
    disciplines = Discipline.objects.all()
    return render(request, 'home.html', {'disciplines': disciplines})

@login_required
def subject_list(request, discipline_id):
    discipline = get_object_or_404(Discipline, id=discipline_id)
    subjects = Subject.objects.filter(discipline=discipline)
    return render(request, 'subject_list.html', {'discipline': discipline, 'subjects': subjects})

@login_required
def teacher_list(request, subject_id):
    subject = get_object_or_404(Subject, id=subject_id)
    subject_teachers = Teacher.objects.filter(subject=subject)
    return render(request, 'teachers_list.html', {'subject': subject, 'teachers': subject_teachers})

@login_required
def teacher_detail(request, teacher_id):
    teacher = get_object_or_404(Teacher, id=teacher_id)
    pdf_files = PDFFile.objects.filter(teacher=teacher)
    return render(request, 'teacher_detail.html', {'teacher': teacher, 'pdf_files': pdf_files})

@login_required
def upload_pdf(request, teacher_id):
    if not request.user.groups.filter(name='simple').exists():
        return render(request, "permission_student.html")
    
    teacher = get_object_or_404(Teacher, id=teacher_id)  
    pdf_files = PDFFile.objects.filter(teacher=teacher)  

    if request.method == 'POST':
        form = PDFUploadForm(request.POST, request.FILES)
        if form.is_valid():
            pdf_file = form.save(commit=False)  
            pdf_file.teacher = teacher 
            pdf_file.uploaded_by = request.user  
            pdf_file.save() 
            return redirect('upload_pdf', teacher_id=teacher_id)  
    else:
        form = PDFUploadForm()

    return render(request, 'upload_pdf.html', {'teacher': teacher, 'files': pdf_files, 'form': form})



def custom_error_view(request, exception=None, error_code=None):
    context = {
        'error_code': error_code or getattr(exception, 'status_code', None),
        'error_message': str(exception) if exception else None
    }
    return render(request, 'error.html', context, status=context['error_code'])

from django.http import JsonResponse, HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
import subprocess

@login_required
@csrf_exempt  
@require_http_methods(["GET", "POST"])
def ai_chat(request):
    if not request.user.groups.filter(name='student').exists():
        return render(request, "permission_student.html")
    if request.method == "GET":
        # Просто редиректим на целевую страницу
        return HttpResponseRedirect("http://127.0.0.1:8080")

    try:
        data = json.loads(request.body)
        prompt = data.get('prompt', '')
        
        if not prompt:
            return JsonResponse({'error': 'Prompt is required'}, status=400)

        result = subprocess.run(
            ['llama-cli', '-m', 'ml_models/model.gguf'],
            input=prompt + "\n",
            capture_output=True,
            text=True,
            timeout=30 
        )

        return JsonResponse({
            'response': result.stdout.strip(),
            'error': result.stderr.strip() if result.stderr else None
        })

    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except subprocess.TimeoutExpired:
        return JsonResponse({'error': 'Request timeout'}, status=504)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
