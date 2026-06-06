from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.urls import reverse
from core.models import Department, Student, Subject, StudentSubject
from core.forms import DepartmentForm, StudentForm, SubjectForm, MarksForm, EnrollForm
from bson import ObjectId
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
import csv
from django.http import HttpResponse
import csv, io
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.contrib.auth.decorators import login_required
from core.models import Department, Batch, Student, Subject, StudentSubject
from core.forms import DepartmentForm, StudentForm, SubjectForm, MarksForm, EnrollForm, BatchForm
from core.forms import CSVImportForm  # add this line

# Home/Dashboard
@login_required
def index(request):
    total_departments = Department.objects.count()
    total_students = Student.objects.count()
    total_subjects = Subject.objects.count()
    total_marks = StudentSubject.objects.count()
    
    recent_students = Student.objects.order_by('-id')[:5]
    recent_subjects = Subject.objects.order_by('-id')[:5]
    
    # Department-wise statistics using batches (instead of direct department on Student)
    dept_stats = []
    for dept in Department.objects:
        # Get all batches under this department
        batches = Batch.objects(department=dept)
        # Count students in any of these batches
        student_count = Student.objects(batch__in=batches).count()
        subject_count = Subject.objects(department=dept).count()
        marks_count = StudentSubject.objects(student__in=Student.objects(batch__in=batches)).count()
        dept_stats.append({
            'dept': dept,
            'student_count': student_count,
            'subject_count': subject_count,
            'marks_count': marks_count
        })
    
    context = {
        'total_departments': total_departments,
        'total_students': total_students,
        'total_subjects': total_subjects,
        'total_marks': total_marks,
        'recent_students': recent_students,
        'recent_subjects': recent_subjects,
        'dept_stats': dept_stats,
    }
    return render(request, 'core/index.html', context)

# Batch Views
@login_required
def batch_list(request):
    batches = Batch.objects.all()
    return render(request, 'core/batch_list.html', {'batches': batches})

@login_required
def batch_add(request):
    if request.method == 'POST':
        form = BatchForm(request.POST)
        if form.is_valid():
            dept_id = form.cleaned_data['department']
            dept = Department.objects.get(id=ObjectId(dept_id))
            batch = Batch(
                name=form.cleaned_data['name'],
                start_year=form.cleaned_data['start_year'],
                department=dept
            )
            batch.save()
            messages.success(request, 'Batch added successfully!')
            return redirect('batch_list')
    else:
        form = BatchForm()
    return render(request, 'core/batch_form.html', {'form': form, 'title': 'Add Batch'})

@login_required
def batch_edit(request, batch_id):
    batch = Batch.objects.get(id=ObjectId(batch_id))
    if request.method == 'POST':
        form = BatchForm(request.POST)
        if form.is_valid():
            dept_id = form.cleaned_data['department']
            dept = Department.objects.get(id=ObjectId(dept_id))
            batch.name = form.cleaned_data['name']
            batch.start_year = form.cleaned_data['start_year']
            batch.department = dept
            batch.save()
            messages.success(request, 'Batch updated successfully!')
            return redirect('batch_list')
    else:
        form = BatchForm(initial={
            'name': batch.name,
            'start_year': batch.start_year,
            'department': str(batch.department.id)
        })
    return render(request, 'core/batch_form.html', {'form': form, 'title': 'Edit Batch'})

@login_required
def batch_delete(request, batch_id):
    batch = Batch.objects.get(id=ObjectId(batch_id))
    if request.method == 'POST':
        if Student.objects(batch=batch).count() > 0:
            messages.error(request, 'Cannot delete batch with enrolled students!')
        else:
            batch.delete()
            messages.success(request, 'Batch deleted successfully!')
            return redirect('batch_list')
    return render(request, 'core/batch_confirm_delete.html', {'batch': batch})

# Department Views
@login_required
def department_list(request):
    departments = Department.objects.all()
    return render(request, 'core/department_list.html', {'departments': departments})

@login_required
def department_add(request):
    if request.method == 'POST':
        form = DepartmentForm(request.POST)
        if form.is_valid():
            department = Department(
                name=form.cleaned_data['name'],
                code=form.cleaned_data['code'],
                description=form.cleaned_data.get('description', ''),
                established_year=form.cleaned_data.get('established_year')
            )
            department.save()
            messages.success(request, 'Department added successfully!')
            return redirect('department_list')
    else:
        form = DepartmentForm()
    return render(request, 'core/department_form.html', {'form': form, 'title': 'Add Department'})

@login_required
def department_edit(request, dept_id):
    department = Department.objects.get(id=ObjectId(dept_id))
    if request.method == 'POST':
        form = DepartmentForm(request.POST)
        if form.is_valid():
            department.name = form.cleaned_data['name']
            department.code = form.cleaned_data['code']
            department.description = form.cleaned_data.get('description', '')
            department.established_year = form.cleaned_data.get('established_year')
            department.save()
            messages.success(request, 'Department updated successfully!')
            return redirect('department_list')
    else:
        form = DepartmentForm(initial={
            'name': department.name,
            'code': department.code,
            'description': department.description,
            'established_year': department.established_year
        })
    return render(request, 'core/department_form.html', {'form': form, 'title': 'Edit Department'})

@login_required
def department_delete(request, dept_id):
    department = Department.objects.get(id=ObjectId(dept_id))
    if request.method == 'POST':
        # Check if department has students or subjects
        if Student.objects(department=department).count() > 0:
            messages.error(request, 'Cannot delete department with enrolled students!')
        elif Subject.objects(department=department).count() > 0:
            messages.error(request, 'Cannot delete department with associated subjects!')
        else:
            department.delete()
            messages.success(request, 'Department deleted successfully!')
            return redirect('department_list')
    return render(request, 'core/department_confirm_delete.html', {'department': department})

# Student Views
@login_required
def student_list(request):
    department_id = request.GET.get('department')
    if department_id:
        department = Department.objects.get(id=ObjectId(department_id))
        batches = Batch.objects(department=department)
        students = Student.objects(batch__in=batches)
        selected_dept = department
    else:
        students = Student.objects.all()
        selected_dept = None
    
    departments = Department.objects.all()
    
    student_data = []
    for student in students:
        total_subjects = student.get_total_subjects()
        passed = student.get_passed_subjects()
        failed = student.get_failed_subjects()
        student_data.append({
            'student': student,
            'total_subjects': total_subjects,
            'passed': passed,
            'failed': failed,
            'status': student.get_overall_status()
        })
    
    context = {
        'students': student_data,
        'departments': departments,
        'selected_dept': selected_dept
    }
    return render(request, 'core/student_list.html', context)

@login_required
def student_add(request):
    if request.method == 'POST':
        form = StudentForm(request.POST)
        if form.is_valid():
            batch_id = form.cleaned_data['batch']
            batch = Batch.objects.get(id=ObjectId(batch_id))
            student = Student(
                name=form.cleaned_data['name'],
                roll_number=form.cleaned_data['roll_number'],
                email=form.cleaned_data['email'],
                batch=batch,
                enrollment_year=form.cleaned_data['enrollment_year'],
                phone=form.cleaned_data.get('phone', ''),
                address=form.cleaned_data.get('address', '')
            )
            student.save()
            messages.success(request, 'Student added successfully!')
            return redirect('student_list')
    else:
        form = StudentForm()
    return render(request, 'core/student_form.html', {'form': form, 'title': 'Add Student'})

@login_required
def student_edit(request, student_id):
    student = Student.objects.get(id=ObjectId(student_id))
    if request.method == 'POST':
        form = StudentForm(request.POST)
        if form.is_valid():
            batch_id = form.cleaned_data['batch']
            batch = Batch.objects.get(id=ObjectId(batch_id))
            student.name = form.cleaned_data['name']
            student.roll_number = form.cleaned_data['roll_number']
            student.email = form.cleaned_data['email']
            student.batch = batch
            student.enrollment_year = form.cleaned_data['enrollment_year']
            student.phone = form.cleaned_data.get('phone', '')
            student.address = form.cleaned_data.get('address', '')
            student.save()
            messages.success(request, 'Student updated successfully!')
            return redirect('student_list')
    else:
        form = StudentForm(initial={
            'name': student.name,
            'roll_number': student.roll_number,
            'email': student.email,
            'batch': str(student.batch.id),
            'enrollment_year': student.enrollment_year,
            'phone': student.phone,
            'address': student.address
        })
    return render(request, 'core/student_form.html', {'form': form, 'title': 'Edit Student'})

@login_required
def student_detail(request, student_id):
    student = Student.objects.get(id=ObjectId(student_id))
    enrollments = StudentSubject.objects(student=student)
    
    marks_data = []
    total_marks = 0
    for enrollment in enrollments:
        marks_data.append({
            'subject': enrollment.subject,
            'score': enrollment.score,
            'attendance': enrollment.attendance_percentage,
            'passed': enrollment.passed,
            'max_marks': enrollment.subject.max_marks,
            'passing_marks': enrollment.subject.passing_marks
        })
        total_marks += enrollment.score
    
    context = {
        'student': student,
        'marks_data': marks_data,
        'total_subjects': len(marks_data),
        'passed_count': sum(1 for m in marks_data if m['passed']),
        'failed_count': sum(1 for m in marks_data if not m['passed'])
    }
    return render(request, 'core/student_detail.html', context)

@login_required
def student_delete(request, student_id):
    student = Student.objects.get(id=ObjectId(student_id))
    if request.method == 'POST':
        # Delete all related StudentSubject records
        StudentSubject.objects(student=student).delete()
        student.delete()
        messages.success(request, 'Student deleted successfully!')
        return redirect('student_list')
    return render(request, 'core/student_confirm_delete.html', {'student': student})

# Subject Views
@login_required
def subject_list(request):
    department_id = request.GET.get('department')
    if department_id:
        department = Department.objects.get(id=ObjectId(department_id))
        subjects = Subject.objects(department=department)
        selected_dept = department
    else:
        subjects = Subject.objects.all()
        selected_dept = None
    
    departments = Department.objects.all()
    
    subject_data = []
    for subject in subjects:
        enrollment_count = StudentSubject.objects(subject=subject).count()
        avg_score = 0
        scores = StudentSubject.objects(subject=subject)
        if scores:
            avg_score = sum(s.score for s in scores) / len(scores)
        subject_data.append({
            'subject': subject,
            'enrollment_count': enrollment_count,
            'avg_score': round(avg_score, 2)
        })
    
    context = {
        'subjects': subject_data,
        'departments': departments,
        'selected_dept': selected_dept
    }
    return render(request, 'core/subject_list.html', context)

@login_required
def subject_add(request):
    if request.method == 'POST':
        form = SubjectForm(request.POST)
        if form.is_valid():
            department_id = form.cleaned_data['department']
            department = Department.objects.get(id=ObjectId(department_id))
            subject = Subject(
                name=form.cleaned_data['name'],
                code=form.cleaned_data['code'],
                department=department,
                semester=form.cleaned_data['semester'],   # ✅ added semester
                credits=form.cleaned_data.get('credits', 3),
                passing_marks=form.cleaned_data.get('passing_marks', 40),
                max_marks=form.cleaned_data.get('max_marks', 100)
            )
            subject.save()
            messages.success(request, 'Subject added successfully!')
            return redirect('subject_list')
    else:
        form = SubjectForm()
    return render(request, 'core/subject_form.html', {'form': form, 'title': 'Add Subject'})

@login_required
def subject_edit(request, subject_id):
    subject = Subject.objects.get(id=ObjectId(subject_id))
    if request.method == 'POST':
        form = SubjectForm(request.POST)
        if form.is_valid():
            department_id = form.cleaned_data['department']
            department = Department.objects.get(id=ObjectId(department_id))
            subject.name = form.cleaned_data['name']
            subject.code = form.cleaned_data['code']
            subject.department = department
            subject.semester = form.cleaned_data['semester']   # ✅ added semester
            subject.credits = form.cleaned_data.get('credits', 3)
            subject.passing_marks = form.cleaned_data.get('passing_marks', 40)
            subject.max_marks = form.cleaned_data.get('max_marks', 100)
            subject.save()
            # Update pass/fail for all enrollments of this subject
            for enrollment in StudentSubject.objects(subject=subject):
                enrollment.save()
            messages.success(request, 'Subject updated successfully!')
            return redirect('subject_list')
    else:
        form = SubjectForm(initial={
            'name': subject.name,
            'code': subject.code,
            'department': str(subject.department.id),
            'semester': subject.semester,   # ✅ added semester
            'credits': subject.credits,
            'passing_marks': subject.passing_marks,
            'max_marks': subject.max_marks
        })
    return render(request, 'core/subject_form.html', {'form': form, 'title': 'Edit Subject'})

@login_required
def subject_delete(request, subject_id):
    subject = Subject.objects.get(id=ObjectId(subject_id))
    if request.method == 'POST':
        # Delete all related enrollments
        StudentSubject.objects(subject=subject).delete()
        subject.delete()
        messages.success(request, 'Subject deleted successfully!')
        return redirect('subject_list')
    return render(request, 'core/subject_confirm_delete.html', {'subject': subject})

# Marks Views
@login_required
def marks_list(request):
    department_id = request.GET.get('department')
    if department_id:
        department = Department.objects.get(id=ObjectId(department_id))
        batches = Batch.objects(department=department)
        students = Student.objects(batch__in=batches)
        selected_dept = department
    else:
        students = Student.objects.all()
        selected_dept = None
    
    departments = Department.objects.all()
    
    marks_data = []
    for student in students:
        enrollments = StudentSubject.objects(student=student)
        for enrollment in enrollments:
            marks_data.append({
                'student': student,
                'subject': enrollment.subject,
                'score': enrollment.score,
                'attendance': enrollment.attendance_percentage,
                'passed': enrollment.passed,
                'id': str(enrollment.id)
            })
    
    context = {
        'marks_list': marks_data,
        'departments': departments,
        'selected_dept': selected_dept
    }
    return render(request, 'core/marks_list.html', context)

@login_required
def marks_add(request):
    department_id = request.GET.get('dept_id') or request.POST.get('dept_id')
    if not department_id and request.method == 'GET':
        departments = Department.objects.all()
        return render(request, 'core/select_department.html', {'departments': departments, 'action': 'marks_add'})
    
    if request.method == 'POST':
        form = MarksForm(request.POST, department_id=department_id)
        if form.is_valid():
            student_id = form.cleaned_data['student']
            subject_id = form.cleaned_data['subject']
            score = form.cleaned_data['score']
            attendance = form.cleaned_data.get('attendance_percentage')
            
            student = Student.objects.get(id=ObjectId(student_id))
            subject = Subject.objects.get(id=ObjectId(subject_id))
            
            # Check if entry exists
            existing = StudentSubject.objects(student=student, subject=subject).first()
            if existing:
                existing.score = score
                existing.attendance_percentage = attendance
                existing.save()
                messages.success(request, 'Marks updated successfully!')
            else:
                enrollment = StudentSubject(
                    student=student,
                    subject=subject,
                    score=score,
                    attendance_percentage=attendance
                )
                enrollment.save()
                messages.success(request, 'Marks added successfully!')
            return redirect('marks_list')
    else:
        form = MarksForm(department_id=department_id)
    
    department = Department.objects.get(id=ObjectId(department_id))
    return render(request, 'core/marks_form.html', {'form': form, 'department': department, 'title': 'Add/Edit Marks'})

@login_required
def marks_edit(request, marks_id):
    marks = StudentSubject.objects.get(id=ObjectId(marks_id))
    department = marks.student.department
    
    if request.method == 'POST':
        form = MarksForm(request.POST, department_id=str(department.id))
        if form.is_valid():
            marks.score = form.cleaned_data['score']
            marks.attendance_percentage = form.cleaned_data.get('attendance_percentage')
            marks.save()
            messages.success(request, 'Marks updated successfully!')
            return redirect('marks_list')
    else:
        form = MarksForm(initial={
            'student': str(marks.student.id),
            'subject': str(marks.subject.id),
            'score': marks.score,
            'attendance_percentage': marks.attendance_percentage
        }, department_id=str(department.id))
    
    return render(request, 'core/marks_form.html', {'form': form, 'department': department, 'title': 'Edit Marks'})

@login_required
def marks_delete(request, marks_id):
    marks = StudentSubject.objects.get(id=ObjectId(marks_id))
    if request.method == 'POST':
        marks.delete()
        messages.success(request, 'Marks record deleted successfully!')
        return redirect('marks_list')
    return render(request, 'core/marks_confirm_delete.html', {'marks': marks})

# Bulk Enrollment
@login_required
def enroll_subjects(request):
    department_id = request.GET.get('dept_id') or request.POST.get('dept_id')
    if not department_id and request.method == 'GET':
        departments = Department.objects.all()
        return render(request, 'core/select_department.html', {'departments': departments, 'action': 'enroll'})
    
    if request.method == 'POST':
        form = EnrollForm(request.POST, department_id=department_id)
        if form.is_valid():
            student_id = form.cleaned_data['student']
            subject_ids = form.cleaned_data['subjects']
            
            student = Student.objects.get(id=ObjectId(student_id))
            for subject_id in subject_ids:
                subject = Subject.objects.get(id=ObjectId(subject_id))
                existing = StudentSubject.objects(student=student, subject=subject).first()
                if not existing:
                    enrollment = StudentSubject(
                        student=student,
                        subject=subject,
                        score=0.0,
                        attendance_percentage=None
                    )
                    enrollment.save()
            messages.success(request, 'Student enrolled in selected subjects!')
            return redirect('student_detail', student_id=student_id)
    else:
        form = EnrollForm(department_id=department_id)
    
    department = Department.objects.get(id=ObjectId(department_id))
    return render(request, 'core/enroll_subjects.html', {'form': form, 'department': department})


def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Registration successful!')
            return redirect('index')
    else:
        form = UserCreationForm()
    return render(request, 'core/register.html', {'form': form})

@login_required
def search(request):
    query = request.GET.get('q', '')
    students = []
    subjects = []
    departments = []
    
    if query:
        # Use Q objects for OR queries in mongoengine
        from mongoengine.queryset.visitor import Q
        students = Student.objects(Q(name__icontains=query) | Q(roll_number__icontains=query))
        subjects = Subject.objects(Q(name__icontains=query) | Q(code__icontains=query))
        departments = Department.objects(Q(name__icontains=query) | Q(code__icontains=query))
    
    context = {
        'query': query,
        'students': students,
        'subjects': subjects,
        'departments': departments,
    }
    return render(request, 'core/search_results.html', context)

@login_required
def export_students_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="students.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Roll Number', 'Name', 'Email', 'Batch', 'Department', 'Enrollment Year', 'Phone', 'Address'])
    
    students = Student.objects.all()
    for student in students:
        writer.writerow([
            student.roll_number, student.name, student.email,
            student.batch.name, student.batch.department.name,
            student.enrollment_year, student.phone, student.address
        ])
    return response

@login_required
def export_marks_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="marks.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Student Name', 'Roll Number', 'Subject', 'Score', 'Max Marks', 'Percentage', 'Pass/Fail', 'Grade'])
    
    enrollments = StudentSubject.objects.all()
    for enrollment in enrollments:
        percentage = (enrollment.score / enrollment.subject.max_marks) * 100 if enrollment.subject.max_marks else 0
        writer.writerow([
            enrollment.student.name, enrollment.student.roll_number,
            enrollment.subject.name, enrollment.score, enrollment.subject.max_marks,
            f"{percentage:.2f}%", 'Pass' if enrollment.passed else 'Fail',
            enrollment.get_grade()
        ])
    return response

@login_required
def import_students(request):
    if request.method == 'POST':
        form = CSVImportForm(request.POST, request.FILES)
        if form.is_valid():
            csv_file = request.FILES['csv_file']
            if not csv_file.name.endswith('.csv'):
                messages.error(request, 'File is not CSV format')
                return redirect('student_list')
            
            data_set = csv_file.read().decode('UTF-8')
            io_string = io.StringIO(data_set)
            next(io_string)  # Skip header
            created_count = 0
            error_count = 0
            
            for row in csv.reader(io_string, delimiter=','):
                if len(row) >= 5:
                    roll_number, name, email, batch_name, enrollment_year = row[0:5]
                    phone = row[5] if len(row) > 5 else ''
                    address = row[6] if len(row) > 6 else ''
                    
                    # Validate
                    if Student.objects(roll_number=roll_number).first():
                        error_count += 1
                        continue
                    try:
                        validate_email(email)
                    except ValidationError:
                        error_count += 1
                        continue
                    
                    # Find batch by name (case-insensitive)
                    batch = Batch.objects(name__iexact=batch_name.strip()).first()
                    if not batch:
                        error_count += 1
                        continue
                    
                    try:
                        enrollment_year = int(enrollment_year)
                    except ValueError:
                        error_count += 1
                        continue
                    
                    student = Student(
                        name=name,
                        roll_number=roll_number,
                        email=email,
                        batch=batch,
                        enrollment_year=enrollment_year,
                        phone=phone,
                        address=address
                    )
                    student.save()
                    created_count += 1
            
            messages.success(request, f'Imported {created_count} students. Errors: {error_count}')
            return redirect('student_list')
    else:
        form = CSVImportForm()
    return render(request, 'core/import_students.html', {'form': form})