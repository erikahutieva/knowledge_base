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

openai.api_key = settings.OPENAI_API_KEY

@login_required
def chat(request):
    if not request.user.has_perm('teach'):
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



def custom_error_view(request, exception=None, error_code=None):
    context = {
        'error_code': error_code or getattr(exception, 'status_code', None),
        'error_message': str(exception) if exception else None
    }
    return render(request, 'error.html', context, status=context['error_code'])



from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
import subprocess
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
import subprocess
import json



@csrf_exempt  
@require_http_methods(["POST"])
def ai_chat(request):
    try:
        data = json.loads(request.body)
        prompt = data.get('prompt', '')
        
        if not prompt:
            return JsonResponse({'error': 'Prompt is required'}, status=400)

        result = subprocess.run(
            ['llama-cli', ' --color -m ', 'ml_models/model.gguf'],
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
    
from django.shortcuts import render
from django.http import JsonResponse
import subprocess
import os
import logging

logger = logging.getLogger(__name__)

def llama_page(request):
    return render(request, "chat.html")

def llama_response(request):
    prompt = request.GET.get("prompt", "").strip()
    if not prompt:
        return JsonResponse({"error": "Пустой запрос"}, status=400)

    try:
        # Формируем полный промпт с инструкциями
        full_prompt = f"[INST] {prompt} [/INST]"
        
        logger.info(f"Отправка запроса к модели: {prompt}")
        
        result = subprocess.run(
            ["llama-cli", "-m", "/Users/erika/Downloads/mistral-7b-instruct-v0.2.Q4_K_M.gguf", 
             "-p", full_prompt, "--no-interactive", "--temp", "0.7", "--ctx-size", "4096"],
            capture_output=True,
            text=True,
            timeout=300,
            env={**os.environ, "PYTHONUNBUFFERED": "1"}
        )
        

        logger.debug(f"Полный вывод модели: {result.stdout}")
 
        output = result.stdout.strip()
        if "[/INST]" in output:
            output = output.split("[/INST]")[-1].strip()
        

        output = output.replace("<s>", "").replace("</s>", "").strip()
        
        logger.info(f"Получен ответ от модели: {output[:200]}...")  
        
        return JsonResponse({"response": output})
    
    except subprocess.TimeoutExpired:
        logger.error("Таймаут запроса к модели")
        return JsonResponse({"error": "Модель не ответила за отведенное время"}, status=504)
    except Exception as e:
        logger.error(f"Ошибка при запросе к модели: {str(e)}")
        return JsonResponse({"error": f"Внутренняя ошибка сервера: {str(e)}"}, status=500)