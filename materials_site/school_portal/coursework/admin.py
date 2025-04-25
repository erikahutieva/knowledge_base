from django.contrib import admin
from .models import Discipline, Subject, Teacher, PDFFile

@admin.register(Discipline)
class DisciplineAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',) 

@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'discipline')
    list_filter = ('discipline',)
    search_fields = ('name',) 

@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ('name', 'subject')
    search_fields = ('name',)  

@admin.register(PDFFile)
class PDFFileAdmin(admin.ModelAdmin):
    list_display = ('file', 'teacher')  
    list_filter = ('teacher', 'uploaded_at')
    search_fields = ('file',)  
