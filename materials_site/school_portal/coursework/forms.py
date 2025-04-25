from django import forms
from .models import Discipline, Subject, Teacher, PDFFile

class DisciplineForm(forms.ModelForm):
    class Meta:
        model = Discipline
        fields = ['name']

class SubjectForm(forms.ModelForm):
    class Meta:
        model = Subject
        fields = ['discipline', 'name']

class TeacherForm(forms.ModelForm):
    class Meta:
        model = Teacher
        fields = ['subject', 'name']

class PDFUploadForm(forms.ModelForm):
    subject = forms.ModelChoiceField(queryset=Subject.objects.all(), label='Выберите предмет')  # Added subject selection field

    class Meta:
        model = PDFFile
        fields = ['file', 'subject']  # Added field for selecting subject

class DynamicForm(forms.Form):
    discipline = forms.ModelChoiceField(
        queryset=Discipline.objects.all(), label='Выберите дисциплину', empty_label="Выберите дисциплину"
    )
    subject = forms.ModelChoiceField(
        queryset=Subject.objects.none(), label='Выберите предмет', required=False, empty_label="Выберите предмет"
    )
    teacher = forms.ModelChoiceField(
        queryset=Teacher.objects.none(), label='Выберите преподавателя', required=False, empty_label="Выберите преподавателя"
    )
    pdf_file = forms.ModelChoiceField(
        queryset=PDFFile.objects.none(), label='Выберите файл', required=False, empty_label="Выберите файл"
    )

    def __init__(self, *args, **kwargs):
        super(DynamicForm, self).__init__(*args, **kwargs)
        if 'discipline' in self.data:
            try:
                discipline_id = int(self.data.get('discipline'))
                self.fields['subject'].queryset = Subject.objects.filter(discipline_id=discipline_id).order_by('name')
            except (ValueError, TypeError):
                pass  # If discipline is invalid, keep it empty
        elif self.instance.pk:
            self.fields['subject'].queryset = self.instance.discipline.subject_set.order_by('name')

# Removed duplicate PDFFileForm to avoid redundancy
