
from django.urls import path

from .views import (
    UserRegistrationView,
    TaskListView,
    TaskCreateView,
    TaskUpdateView,
    TaskDeleteView,
    TaskKanbanView,
    update_task_status,
    TaskCalendarView,
    TaskAnalyticsView,
    ProfileUpdateView,
)

app_name = 'tasks'

urlpatterns = [
    path('register/', UserRegistrationView.as_view(), name='register'),

    path('', TaskListView.as_view(), name='task_list'),
    path('board/', TaskKanbanView.as_view(), name='task_kanban'),
    path('calendar/', TaskCalendarView.as_view(), name='task_calendar'),
    path('analytics/', TaskAnalyticsView.as_view(), name='task_analytics'),
    path('account/', ProfileUpdateView.as_view(), name='profile'),
    path('task/<int:pk>/status/', update_task_status, name='task_status_update'),

    path('create/', TaskCreateView.as_view(), name='task_create'),

    path(
        'edit/<int:pk>/',
        TaskUpdateView.as_view(),
        name='task_update'
    ),

    path(
        'delete/<int:pk>/',
        TaskDeleteView.as_view(),
        name='task_delete'
    ),
]
