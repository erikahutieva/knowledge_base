from django.contrib import admin
from .models import Discipline, Subject, Teacher, PDFFile

@admin.register(Discipline)
class DisciplineAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)  # Добавлен поиск по имени дисциплины

@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'discipline')
    list_filter = ('discipline',)
    search_fields = ('name',)  # Добавлен поиск по имени предмета

@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ('name', 'subject')
    search_fields = ('name',)  # Добавлен поиск по имени преподавателя

@admin.register(PDFFile)
class PDFFileAdmin(admin.ModelAdmin):
    list_display = ('file', 'teacher')  # Выводим информацию о файле, преподавателе и дате загрузки
    list_filter = ('teacher', 'uploaded_at')  # Добавляем фильтрацию по преподавателям и дате загрузки
    search_fields = ('file',)  # Добавлен поиск по имени файла
