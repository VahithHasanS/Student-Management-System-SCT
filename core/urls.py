from django.urls import path
from core import views

urlpatterns = [
    # Home
    path('', views.index, name='index'),
    
    # Departments
    path('departments/', views.department_list, name='department_list'),
    path('departments/add/', views.department_add, name='department_add'),
    path('departments/edit/<str:dept_id>/', views.department_edit, name='department_edit'),
    path('departments/delete/<str:dept_id>/', views.department_delete, name='department_delete'),
    
    # Students
    path('students/', views.student_list, name='student_list'),
    path('students/add/', views.student_add, name='student_add'),
    path('students/edit/<str:student_id>/', views.student_edit, name='student_edit'),
    path('students/delete/<str:student_id>/', views.student_delete, name='student_delete'),
    path('students/<str:student_id>/', views.student_detail, name='student_detail'),
    
    # Subjects
    path('subjects/', views.subject_list, name='subject_list'),
    path('subjects/add/', views.subject_add, name='subject_add'),
    path('subjects/edit/<str:subject_id>/', views.subject_edit, name='subject_edit'),
    path('subjects/delete/<str:subject_id>/', views.subject_delete, name='subject_delete'),
    
    # Marks
    path('marks/', views.marks_list, name='marks_list'),
    path('marks/add/', views.marks_add, name='marks_add'),
    path('marks/edit/<str:marks_id>/', views.marks_edit, name='marks_edit'),
    path('marks/delete/<str:marks_id>/', views.marks_delete, name='marks_delete'),
    
    # Enrollment
    path('enroll/', views.enroll_subjects, name='enroll_subjects'),
    path('register/', views.register, name='register'),
    path('search/', views.search, name='search'),
    path('export/students/', views.export_students_csv, name='export_students'),
    path('export/marks/', views.export_marks_csv, name='export_marks'),
    path('import/students/', views.import_students, name='import_students'),
    path('batches/', views.batch_list, name='batch_list'),
    path('batches/add/', views.batch_add, name='batch_add'),
    path('batches/edit/<str:batch_id>/', views.batch_edit, name='batch_edit'),
    path('batches/delete/<str:batch_id>/', views.batch_delete, name='batch_delete'),
]