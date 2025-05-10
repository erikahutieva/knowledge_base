from django.contrib import admin
from .models import Discipline, Subject, Teacher, PDFFile
# Админка для Discipline: отображение и поиск по имени
@admin.register(Discipline)
class DisciplineAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

# Админка для Subject: имя, дисциплина, фильтр и поиск
@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'discipline')
    list_filter = ('discipline',)
    search_fields = ('name',)

# Админка для Teacher: имя, предмет, поиск
@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ('name', 'subject')
    search_fields = ('name',)

# Админка для PDFFile: файл, преподаватель, фильтр и поиск
@admin.register(PDFFile)
class PDFFileAdmin(admin.ModelAdmin):
    list_display = ('file', 'teacher')
    list_filter = ('teacher', 'uploaded_at')
    search_fields = ('file',)



