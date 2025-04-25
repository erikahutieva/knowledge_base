import os
from django.core.files.storage import FileSystemStorage
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseForbidden, JsonResponse
from .models import Discipline, Subject, Teacher, PDFFile, model
from .forms import PDFUploadForm
from django.conf import settings
import openai
from PIL import Image
import pytesseract
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q

def login_view(request):
    """
    Функция для входа пользователя.
    При POST-запросе получает логин и пароль из формы,
    проверяет их с помощью функции authenticate и, если данные корректны, выполняет вход.
    После успешной авторизации происходит перенаправление на home.html.
    """
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
    """
    Функция для выхода пользователя.
    """
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
    if not request.user.has_perm('your_app_label.can_upload_pdf'):
        return HttpResponseForbidden("У вас нет прав для загрузки PDF файлов.")
    
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

openai.api_key = settings.OPENAI_API_KEY

@login_required
def chat(request):
    if not request.user.has_perm('your_app_label.can_chat'):
        return HttpResponseForbidden("У вас нет прав для доступа к чату.")
    
    context = {}
    if request.method == "POST":
        user_message = request.POST.get("message", "").strip()
        photo = request.FILES.get("photo")
        image_text = ""
        
        if photo:
            try:
                fs = FileSystemStorage(location=os.path.join(settings.MEDIA_ROOT, "chat_photos"))
                if not os.path.exists(fs.location):
                    os.makedirs(fs.location)
                filename = fs.save(photo.name, photo)
                photo_path = os.path.join(fs.location, filename)
                try:
                    image = Image.open(photo_path)
                    image_text = pytesseract.image_to_string(image)
                except Exception as ocr_error:
                    context["error"] = f"Ошибка при обработке изображения: {ocr_error}"
            except Exception as e:
                context["error"] = f"Ошибка при сохранении изображения: {e}"
        
        combined_message = user_message
        if image_text:
            combined_message += "\n\n[Содержимое изображения]:\n" + image_text.strip()
        
        if combined_message.strip():
            try:
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "Ты – полезный помощник. Ответь с учетом текста и содержимого изображения, если оно присутствует."},
                        {"role": "user", "content": combined_message}
                    ]
                )
                assistant_message = response.choices[0].message.content
                context.update({
                    "user_message": user_message,
                    "assistant_message": assistant_message,
                })
            except Exception as e:
                context["error"] = f"Ошибка при обращении к API: {e}"
        else:
            context["error"] = "Пожалуйста, введите текстовое сообщение или отправьте фото."
    return render(request, "chat.html", context)

@login_required
def ai_chat(request):
    """Представление для чата с Mistral моделью"""
    if request.method == 'POST':
        message = request.POST.get('message', '').strip()
        if message:
            try:
                # Генерация ответа с помощью модели
                response = model.generate(message)
                return render(request, 'chat_ai.html', {
                    'user_message': message,
                    'assistant_message': response
                })
            except Exception as e:
                messages.error(request, f"Ошибка при генерации ответа: {str(e)}")
        else:
            messages.error(request, "Пожалуйста, введите сообщение")
    
    return render(request, 'chat_ai.html')


@csrf_exempt
def chat_api(request):
    """API для обработки запросов чата с Mistral моделью"""
    if request.method == 'POST':
        prompt = request.POST.get('message', '')
        try:
            response = model.generate(prompt)
            return JsonResponse({
                'success': True,
                'response': response
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
    return JsonResponse({
        'success': False,
        'error': 'Invalid request method'
    }, status=400)

@login_required
def search(request):
    """Поиск по PDF файлам и взаимодействие с моделью"""
    query = request.GET.get('q', '').strip()
    results = []
    ai_response = None
    
    if query:
        # Поиск PDF файлов
        results = PDFFile.objects.filter(
            Q(custom_name__icontains=query) | 
            Q(teacher__name__icontains=query) |
            Q(teacher__subject__name__icontains=query) |
            Q(teacher__subject__discipline__name__icontains=query)
        ).distinct()
        
        # Получение ответа от AI модели
        try:
            ai_prompt = f"Пользователь ищет информацию по запросу: '{query}'. " \
                        "Дайте краткий ответ или совет по этому запросу."
            ai_response = model.generate(ai_prompt)
        except Exception as e:
            messages.error(request, f"Ошибка при обращении к AI модели: {str(e)}")
    
    return render(request, 'search.html', {
        'query': query,
        'results': results,
        'ai_response': ai_response
    })