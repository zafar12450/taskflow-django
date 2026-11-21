
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q, Count
from django.utils import timezone
from datetime import date, timedelta
import calendar
from django.urls import reverse_lazy
from django.views.generic import (
    ListView,
    CreateView,
    UpdateView,
    DeleteView,
)

from .models import Task
from .forms import TaskForm, UserRegistrationForm, UserProfileForm


class UserRegistrationView(CreateView):

    form_class = UserRegistrationForm
    template_name = 'tasks/register.html'
    success_url = reverse_lazy('tasks:task_list')

    def form_valid(self, form):
        response = super().form_valid(form)

        login(
            self.request,
            self.object,
            backend='django.contrib.auth.backends.ModelBackend'
        )

        return response


class TaskListView(LoginRequiredMixin, ListView):

    model = Task
    template_name = 'tasks/task_list.html'
    context_object_name = 'tasks'

    def get_queryset(self):
        queryset = Task.objects.filter(
            owner=self.request.user
        )

        search = self.request.GET.get('q', '').strip()
        status = self.request.GET.get('status', '')
        priority = self.request.GET.get('priority', '')

        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(description__icontains=search)
            )

        if status:
            queryset = queryset.filter(status=status)

        if priority:
            queryset = queryset.filter(priority=priority)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        user_tasks = Task.objects.filter(
            owner=self.request.user
        )

        context['total_tasks'] = user_tasks.count()

        context['completed_tasks'] = user_tasks.filter(
            status=Task.Status.COMPLETED
        ).count()

        context['pending_tasks'] = user_tasks.filter(
            status=Task.Status.TODO
        ).count()

        context['in_progress_tasks'] = user_tasks.filter(
            status=Task.Status.IN_PROGRESS
        ).count()

        context['status_choices'] = Task.Status.choices
        context['priority_choices'] = Task.Priority.choices

        context['search_query'] = self.request.GET.get('q', '')
        context['selected_status'] = self.request.GET.get('status', '')
        context['selected_priority'] = self.request.GET.get('priority', '')

        return context


class TaskCreateView(LoginRequiredMixin, CreateView):

    model = Task
    form_class = TaskForm
    template_name = 'tasks/task_form.html'
    success_url = reverse_lazy('tasks:task_list')

    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)


class TaskUpdateView(LoginRequiredMixin, UpdateView):

    model = Task
    form_class = TaskForm
    template_name = 'tasks/task_form.html'
    success_url = reverse_lazy('tasks:task_list')

    def get_queryset(self):
        return Task.objects.filter(
            owner=self.request.user
        )


class TaskDeleteView(LoginRequiredMixin, DeleteView):

    model = Task
    template_name = 'tasks/task_confirm_delete.html'
    success_url = reverse_lazy('tasks:task_list')

    def get_queryset(self):
        return Task.objects.filter(
            owner=self.request.user
        )


# Kanban board and secure task status updates
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_POST
from django.views.generic import TemplateView


class TaskKanbanView(LoginRequiredMixin, TemplateView):
    template_name = 'tasks/task_kanban.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user_tasks = Task.objects.filter(owner=self.request.user)
        context['todo_tasks'] = user_tasks.filter(status=Task.Status.TODO)
        context['in_progress_tasks'] = user_tasks.filter(status=Task.Status.IN_PROGRESS)
        context['completed_tasks'] = user_tasks.filter(status=Task.Status.COMPLETED)
        context['total_tasks'] = user_tasks.count()
        return context


@login_required
@require_POST
def update_task_status(request, pk):
    task = get_object_or_404(Task, pk=pk, owner=request.user)
    new_status = request.POST.get('status', '')

    if new_status not in dict(Task.Status.choices):
        return JsonResponse(
            {'success': False, 'error': 'Invalid task status.'},
            status=400,
        )

    task.status = new_status
    task.save(update_fields=['status', 'updated_at'])

    return JsonResponse({
        'success': True,
        'task_id': task.pk,
        'status': task.status,
        'status_label': task.get_status_display(),
    })



# Calendar, overdue tracking, and productivity analytics
class TaskCalendarView(LoginRequiredMixin, TemplateView):
    template_name = 'tasks/calendar.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = timezone.localdate()

        try:
            year = int(self.request.GET.get('year', today.year))
            month = int(self.request.GET.get('month', today.month))
            if month < 1 or month > 12:
                raise ValueError
            selected_month = date(year, month, 1)
        except (TypeError, ValueError):
            selected_month = date(today.year, today.month, 1)

        first_day = selected_month
        last_day = date(
            selected_month.year,
            selected_month.month,
            calendar.monthrange(selected_month.year, selected_month.month)[1],
        )

        month_tasks = Task.objects.filter(
            owner=self.request.user,
            due_date__gte=first_day,
            due_date__lte=last_day,
        ).order_by('due_date', 'priority', 'title')

        tasks_by_day = {}
        for task in month_tasks:
            tasks_by_day.setdefault(task.due_date.day, []).append(task)

        month_grid = calendar.Calendar(firstweekday=0).monthdayscalendar(
            selected_month.year,
            selected_month.month,
        )

        previous_month = (
            date(selected_month.year - 1, 12, 1)
            if selected_month.month == 1
            else date(selected_month.year, selected_month.month - 1, 1)
        )
        next_month = (
            date(selected_month.year + 1, 1, 1)
            if selected_month.month == 12
            else date(selected_month.year, selected_month.month + 1, 1)
        )

        context.update({
            'calendar_year': selected_month.year,
            'calendar_month': selected_month.month,
            'month_name': selected_month.strftime('%B %Y'),
            'weekdays': ['Monday', 'Tuesday', 'Wednesday', 'Thursday',
                         'Friday', 'Saturday', 'Sunday'],
            'month_grid': month_grid,
            'tasks_by_day': tasks_by_day,
            'calendar_days': [
                {'day': day, 'tasks': tasks_by_day.get(day, [])}
                for day in range(1, last_day.day + 1)
            ],
            'today': today,
            'previous_month': previous_month,
            'next_month': next_month,
            'month_task_count': month_tasks.count(),
        })
        return context


class TaskAnalyticsView(LoginRequiredMixin, TemplateView):
    template_name = 'tasks/analytics.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = timezone.localdate()
        user_tasks = Task.objects.filter(owner=self.request.user)

        total = user_tasks.count()
        completed = user_tasks.filter(status=Task.Status.COMPLETED).count()
        pending = user_tasks.filter(status=Task.Status.TODO).count()
        in_progress = user_tasks.filter(status=Task.Status.IN_PROGRESS).count()
        overdue = user_tasks.filter(
            due_date__lt=today
        ).exclude(status=Task.Status.COMPLETED).count()

        priority_counts = {
            'high': user_tasks.filter(priority=Task.Priority.HIGH).count(),
            'medium': user_tasks.filter(priority=Task.Priority.MEDIUM).count(),
            'low': user_tasks.filter(priority=Task.Priority.LOW).count(),
        }

        weekly_activity = []
        for days_ago in range(6, -1, -1):
            day = today - timedelta(days=days_ago)
            count = user_tasks.filter(
                created_at__date=day
            ).count()
            weekly_activity.append({
                'label': day.strftime('%a'),
                'date': day,
                'count': count,
            })

        max_activity = max([item['count'] for item in weekly_activity] + [1])
        for item in weekly_activity:
            item['percentage'] = round(item['count'] / max_activity * 100)

        context.update({
            'total_tasks': total,
            'completed_tasks': completed,
            'pending_tasks': pending,
            'in_progress_tasks': in_progress,
            'overdue_tasks': overdue,
            'completion_rate': round(completed / total * 100) if total else 0,
            'priority_counts': priority_counts,
            'weekly_activity': weekly_activity,
            'today': today,
        })
        return context



class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    """Users can edit only the account linked to their current session."""

    model = User
    form_class = UserProfileForm
    template_name = 'tasks/profile.html'
    success_url = reverse_lazy('tasks:profile')

    def get_object(self, queryset=None):
        return self.request.user
