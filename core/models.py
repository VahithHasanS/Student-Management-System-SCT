from mongoengine import Document, StringField, IntField, FloatField, ReferenceField, ListField, DateTimeField, BooleanField
from datetime import datetime

class Department(Document):
    name = StringField(required=True, max_length=100, unique=True)
    code = StringField(required=True, max_length=10, unique=True)
    description = StringField(max_length=500)
    established_year = IntField()
    total_semesters = IntField(default=8)  # usually 8 semesters

    meta = {'collection': 'departments', 'ordering': ['name']}
    
    def __str__(self):
        return f"{self.name} ({self.code})"

class Batch(Document):
    name = StringField(required=True, max_length=50)  # e.g., "2024 Batch"
    start_year = IntField(required=True)              # e.g., 2024
    department = ReferenceField(Department, required=True, reverse_delete_rule=2)
    
    meta = {'collection': 'batches', 'ordering': ['-start_year'], 'unique_together': ('name', 'department')}
    
    def __str__(self):
        return f"{self.name} - {self.department.code}"

class Student(Document):
    name = StringField(required=True, max_length=200)
    roll_number = StringField(required=True, unique=True, max_length=50)
    email = StringField(required=True, unique=True)
    batch = ReferenceField(Batch, required=True, reverse_delete_rule=2)   # instead of department directly
    enrollment_year = IntField(required=True)
    phone = StringField(max_length=15)
    address = StringField()
    
    meta = {'collection': 'students', 'ordering': ['roll_number'], 'indexes': ['roll_number', 'batch']}
    
    def __str__(self):
        return f"{self.name} ({self.roll_number})"
    
    @property
    def department(self):
        return self.batch.department
    
    def get_total_subjects(self):
        return StudentSubject.objects(student=self).count()
    
    def get_passed_subjects(self):
        return StudentSubject.objects(student=self, passed=True).count()
    
    def get_failed_subjects(self):
        return StudentSubject.objects(student=self, passed=False).count()
    
    def get_overall_status(self):
        total = self.get_total_subjects()
        if total == 0:
            return "No Subjects"
        passed = self.get_passed_subjects()
        if passed == total:
            return "Passed All"
        elif passed > 0:
            return f"Partial ({passed}/{total})"
        else:
            return "Failed All"

class Subject(Document):
    name = StringField(required=True, max_length=200)
    code = StringField(required=True, unique=True, max_length=20)
    department = ReferenceField(Department, required=True, reverse_delete_rule=2)
    semester = IntField(required=True, min_value=1, max_value=8)   # new field
    credits = IntField(default=3)
    passing_marks = FloatField(default=40.0)
    max_marks = FloatField(default=100.0)
    
    meta = {'collection': 'subjects', 'ordering': ['semester', 'code'], 'indexes': ['code', 'department', 'semester']}
    
    def __str__(self):
        return f"{self.name} (Sem {self.semester})"

class StudentSubject(Document):
    student = ReferenceField(Student, required=True, reverse_delete_rule=2)
    subject = ReferenceField(Subject, required=True, reverse_delete_rule=2)
    score = FloatField(required=True, default=0.0, min_value=0)
    attendance_percentage = FloatField(min_value=0, max_value=100, null=True, blank=True)
    passed = BooleanField(default=False)
    recorded_date = DateTimeField(default=datetime.now)
    
    meta = {'collection': 'student_subjects', 'unique_together': ('student', 'subject'), 'indexes': [('student', 'subject'), 'student', 'subject']}
    
    def save(self, *args, **kwargs):
        if self.subject:
            if self.score >= self.subject.passing_marks:
                self.passed = True
            else:
                self.passed = False
        super(StudentSubject, self).save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.student.name} - {self.subject.name}: {self.score}"