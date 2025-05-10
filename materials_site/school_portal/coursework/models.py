from django.db import models
from django.contrib.auth import get_user_model
from django.conf import settings
import os
import subprocess
import json
from django.http import JsonResponse

User = get_user_model()

class Discipline(models.Model):
    name = models.CharField(max_length=200)

    class Meta:
        verbose_name = "Дисциплина"
        verbose_name_plural = "Дисциплины"
        ordering = ['name']

    def __str__(self) -> str:
        return self.name

class Subject(models.Model):
    name = models.CharField(max_length=200)
    discipline = models.ForeignKey(Discipline, on_delete=models.CASCADE, related_name='subjects')

    class Meta:
        verbose_name = "Предмет"
        verbose_name_plural = "Предметы"
        ordering = ['name']

    def __str__(self) -> str:
        return self.name

class Teacher(models.Model):
    name = models.CharField(max_length=200)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='teachers')

    class Meta:
        verbose_name = "Преподаватель"
        verbose_name_plural = "Преподаватели"
        ordering = ['name']

    def __str__(self) -> str:
        return self.name

class PDFFile(models.Model):
    file = models.FileField(upload_to='pdfs/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name='pdf_files')
    custom_name = models.CharField(max_length=200, blank=True)
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='pdf_files', null=True, blank=True)

    class Meta:
        verbose_name = "PDF файл"
        verbose_name_plural = "PDF файлы"
        ordering = ['-uploaded_at']
        permissions = [
            ('can_upload_pdf', 'Разрешение на загрузку PDF файлов'),
        ]

    def __str__(self):
        return self.custom_name if self.custom_name else self.file.name




def query_llama(prompt):
    command = ["llama-cli", "--color", "-m", "ml_models/model.gguf"]
    process = subprocess.Popen(
        command,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    stdout, stderr = process.communicate(input=prompt + "\n")
    
    if stderr:
        return {"error": stderr}
    return {"response": stdout}



#llama-cli --color -m Downloads/mistral-7b-instruct-v0.2.Q4_K_M.gguf 