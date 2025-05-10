import os
import json
import subprocess
import logging

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.core.files.storage import FileSystemStorage
from django.db.models import Q
from django.http import (
    HttpResponseForbidden, JsonResponse, HttpResponse
)
from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from PIL import Image
import pytesseract
import openai

from .models import Discipline, Subject, Teacher, PDFFile, query_llama
from .forms import PDFUploadForm

# Логгер для записи ошибок и служебной информации
logger = logging.getLogger(__name__)

# Аутентификация 

def login_view(request):
    # Обработка формы входа
    if request.method == 'POST':
        user = authenticate(
            request,
            username=request.POST.get('username'),
            password=request.POST.get('password')
        )
        if user:
            login(request, user)
            return redirect('home')
        messages.error(request, 'Неверное имя пользователя или пароль')
    return render(request, 'login.html')


def logout_view(request):
    # Выход из системы
    logout(request)
    return redirect('login')



@login_required
def discipline_list(request):
    # Главная страница со списком дисциплин
    return render(request, 'home.html', {'disciplines': Discipline.objects.all()})


@login_required
def subject_list(request, discipline_id):
    # Список предметов по выбранной дисциплине
    discipline = get_object_or_404(Discipline, id=discipline_id)
    subjects = Subject.objects.filter(discipline=discipline)
    return render(request, 'subject_list.html', {'discipline': discipline, 'subjects': subjects})


@login_required
def teacher_list(request, subject_id):
    # Список преподавателей по предмету
    subject = get_object_or_404(Subject, id=subject_id)
    teachers = Teacher.objects.filter(subject=subject)
    return render(request, 'teachers_list.html', {'subject': subject, 'teachers': teachers})


@login_required
def teacher_detail(request, teacher_id):
    # Детали преподавателя и его файлы
    teacher = get_object_or_404(Teacher, id=teacher_id)
    files = PDFFile.objects.filter(teacher=teacher)
    return render(request, 'teacher_detail.html', {'teacher': teacher, 'pdf_files': files})


@login_required
def upload_pdf(request, teacher_id):
    # Загрузка PDF-файла студентом для преподавателя
    if not request.user.groups.filter(name='simple').exists():
        return render(request, "permission_student.html")

    teacher = get_object_or_404(Teacher, id=teacher_id)
    files = PDFFile.objects.filter(teacher=teacher)

    if request.method == 'POST':
        form = PDFUploadForm(request.POST, request.FILES)
        if form.is_valid():
            instance = form.save(commit=False)
            instance.teacher = teacher
            instance.uploaded_by = request.user
            instance.save()
            return redirect('upload_pdf', teacher_id=teacher_id)
    else:
        form = PDFUploadForm()

    return render(request, 'upload_pdf.html', {'teacher': teacher, 'files': files, 'form': form})



openai.api_key = settings.OPENAI_API_KEY

@login_required
def chat(request):
    # Чат только для пользователей с правами 'teach'
    if not request.user.has_perm('teach'):
        return HttpResponseForbidden("Нет доступа")

    context = {}
    if request.method == "POST":
        user_msg = request.POST.get("message", "").strip()
        photo = request.FILES.get("photo")
        image_text = ""

        # Обработка изображения с помощью OCR
        if photo:
            try:
                fs = FileSystemStorage(location=os.path.join(settings.MEDIA_ROOT, "chat_photos"))
                os.makedirs(fs.location, exist_ok=True)
                path = fs.save(photo.name, photo)
                image = Image.open(os.path.join(fs.location, path))
                image_text = pytesseract.image_to_string(image)
            except Exception as e:
                context["error"] = f"Ошибка изображения: {e}"

        # Объединяем текст из фото и текстовое сообщение
        prompt = user_msg + "\n\n[Содержимое изображения]:\n" + image_text.strip() if image_text else user_msg

        # Отправка в OpenAI GPT
        if prompt.strip():
            try:
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "Ты — полезный помощник."},
                        {"role": "user", "content": prompt}
                    ]
                )
                context["user_message"] = user_msg
                context["assistant_message"] = response.choices[0].message.content
            except Exception as e:
                context["error"] = f"Ошибка API: {e}"
        else:
            context["error"] = "Введите сообщение или фото"
    return render(request, "chat.html", context)




def custom_error_view(request, exception=None, error_code=None):
    # Пользовательская страница ошибки
    context = {
        'error_code': error_code or getattr(exception, 'status_code', None),
        'error_message': str(exception) if exception else None
    }
    return render(request, 'error.html', context, status=context['error_code'])



@csrf_exempt
@require_http_methods(["POST"])
def ai_chat(request):
    # Запрос к LLaMA через subprocess — POST API
    try:
        data = json.loads(request.body)
        prompt = data.get('prompt', '')
        if not prompt:
            return JsonResponse({'error': 'Prompt is required'}, status=400)

        result = subprocess.run(
            ['llama-cli', '-m', 'ml_models/model.gguf', '-p', prompt, '--no-interactive'],
            capture_output=True,
            text=True,
            timeout=30
        )
        return JsonResponse({
            'response': result.stdout.strip(),
            'error': result.stderr.strip() or None
        })

    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except subprocess.TimeoutExpired:
        return JsonResponse({'error': 'Timeout'}, status=504)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def llama_page(request):
    return render(request, "chat.html")


def llama_response(request):
    # Асинхронный GET-запрос к LLaMA с выводом результата
    prompt = request.GET.get("prompt", "").strip()
    if not prompt:
        return JsonResponse({"error": "Пустой запрос"}, status=400)

    try:
        full_prompt = f"[INST] {prompt} [/INST]"

        result = subprocess.run(
            [
                "llama-cli",
                "-m", "/Users/erika/Downloads/mistral-7b-instruct-v0.2.Q4_K_M.gguf",
                "-p", full_prompt,
                "--no-interactive",
                "--temp", "0.7",
                "--ctx-size", "4096"
            ],
            capture_output=True,
            text=True,
            timeout=300,
            env={**os.environ, "PYTHONUNBUFFERED": "1"}
        )

        # Обработка вывода модели
        output = result.stdout.strip()
        if "[/INST]" in output:
            output = output.split("[/INST]")[-1].strip()
        output = output.replace("<s>", "").replace("</s>", "").strip()

        logger.info(f"Ответ модели: {output[:200]}...")
        return JsonResponse({"response": output})

    except subprocess.TimeoutExpired:
        logger.error("Таймаут запроса")
        return JsonResponse({"error": "Таймаут запроса"}, status=504)
    except Exception as e:
        logger.error(f"Ошибка: {str(e)}")
        return JsonResponse({"error": f"Ошибка сервера: {str(e)}"}, status=500)
