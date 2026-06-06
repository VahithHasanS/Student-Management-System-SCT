from django import forms
from core.models import Department, Batch, Student, Subject, StudentSubject
from datetime import datetime

class DepartmentForm(forms.Form):
    name = forms.CharField(max_length=100, required=True)
    code = forms.CharField(max_length=10, required=True)
    description = forms.CharField(widget=forms.Textarea, required=False)
    established_year = forms.IntegerField(required=False, min_value=1900, max_value=datetime.now().year)
    total_semesters = forms.IntegerField(initial=8, min_value=1, max_value=10, required=False)

class BatchForm(forms.Form):
    name = forms.CharField(max_length=50, required=True)
    start_year = forms.IntegerField(min_value=2000, max_value=datetime.now().year+5, required=True)
    department = forms.ChoiceField(choices=[], required=True)
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        departments = Department.objects.all()
        self.fields['department'].choices = [(str(d.id), f"{d.name} ({d.code})") for d in departments]

class StudentForm(forms.Form):
    name = forms.CharField(max_length=200, required=True)
    roll_number = forms.CharField(max_length=50, required=True)
    email = forms.EmailField(required=True)
    batch = forms.ChoiceField(choices=[], required=True)
    enrollment_year = forms.IntegerField(required=True, min_value=2000, max_value=datetime.now().year)
    phone = forms.CharField(max_length=15, required=False)
    address = forms.CharField(widget=forms.Textarea, required=False)
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        batches = Batch.objects.all()
        self.fields['batch'].choices = [(str(b.id), f"{b.name} ({b.department.code})") for b in batches]
    
    def clean_roll_number(self):
        roll = self.cleaned_data['roll_number']
        if Student.objects(roll_number=roll).first():
            raise forms.ValidationError("Roll number already exists")
        return roll
    
    def clean_email(self):
        email = self.cleaned_data['email']
        if Student.objects(email=email).first():
            raise forms.ValidationError("Email already exists")
        return email

class SubjectForm(forms.Form):
    name = forms.CharField(max_length=200, required=True)
    code = forms.CharField(max_length=20, required=True)
    department = forms.ChoiceField(choices=[], required=True)
    semester = forms.IntegerField(min_value=1, max_value=8, required=True)
    credits = forms.IntegerField(min_value=1, max_value=10, required=False, initial=3)
    passing_marks = forms.FloatField(min_value=0, max_value=100, required=False, initial=40)
    max_marks = forms.FloatField(min_value=1, max_value=100, required=False, initial=100)
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        departments = Department.objects.all()
        self.fields['department'].choices = [(str(d.id), f"{d.name} ({d.code})") for d in departments]
    
    def clean_code(self):
        code = self.cleaned_data['code']
        if Subject.objects(code=code).first():
            raise forms.ValidationError("Subject code already exists")
        return code

class MarksForm(forms.Form):
    student = forms.ChoiceField(choices=[], required=True)
    subject = forms.ChoiceField(choices=[], required=True)
    score = forms.FloatField(min_value=0, max_value=100, required=True)
    attendance_percentage = forms.FloatField(min_value=0, max_value=100, required=False)
    
    def __init__(self, *args, department_id=None, **kwargs):
        super().__init__(*args, **kwargs)
        if department_id:
            # Get all batches of this department
            batches = Batch.objects(department=department_id)
            students = Student.objects(batch__in=batches)
            subjects = Subject.objects(department=department_id)
            self.fields['student'].choices = [(str(s.id), f"{s.name} ({s.roll_number})") for s in students]
            self.fields['subject'].choices = [(str(sub.id), f"{sub.name} (Sem {sub.semester})") for sub in subjects]

class EnrollForm(forms.Form):
    student = forms.ChoiceField(choices=[], required=True)
    subjects = forms.MultipleChoiceField(choices=[], required=True, widget=forms.CheckboxSelectMultiple)
    
    def __init__(self, *args, department_id=None, **kwargs):
        super().__init__(*args, **kwargs)
        if department_id:
            batches = Batch.objects(department=department_id)
            students = Student.objects(batch__in=batches)
            subjects = Subject.objects(department=department_id)
            self.fields['student'].choices = [(str(s.id), f"{s.name} ({s.roll_number})") for s in students]
            self.fields['subjects'].choices = [(str(sub.id), f"{sub.name} (Sem {sub.semester})") for sub in subjects]

class BatchForm(forms.Form):
    name = forms.CharField(max_length=50, required=True)
    start_year = forms.IntegerField(min_value=2000, max_value=datetime.now().year+5, required=True)
    department = forms.ChoiceField(choices=[], required=True)
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        departments = Department.objects.all()
        self.fields['department'].choices = [(str(d.id), f"{d.name} ({d.code})") for d in departments]

class CSVImportForm(forms.Form):
    csv_file = forms.FileField(label='Select CSV file', help_text='Format: Roll Number, Name, Email, Batch Name (exactly as in system), Enrollment Year, Phone, Address')