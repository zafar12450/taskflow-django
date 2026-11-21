
from django.contrib.auth.models import User
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse

from .models import Task


class AuthenticationTests(TestCase):
    """Tests for registration, login, logout and access protection."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='StrongPass!2026Secure'
        )

    def test_login_page_loads(self):
        response = self.client.get(reverse('login'))

        self.assertEqual(response.status_code, 200)

    def test_valid_login(self):
        response = self.client.post(
            reverse('login'),
            {
                'username': 'testuser',
                'password': 'StrongPass!2026Secure',
            }
        )

        self.assertRedirects(
            response,
            reverse('tasks:task_list')
        )

    def test_invalid_login(self):
        response = self.client.post(
            reverse('login'),
            {
                'username': 'testuser',
                'password': 'WrongPassword123',
            }
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.wsgi_request.user.is_authenticated)

    def test_logout(self):
        self.client.force_login(self.user)

        response = self.client.post(reverse('logout'))

        self.assertRedirects(response, reverse('login'))

        dashboard_response = self.client.get(
            reverse('tasks:task_list')
        )

        self.assertRedirects(
            dashboard_response,
            f"{reverse('login')}?next=/"
        )

    def test_registration_page_loads(self):
        response = self.client.get(
            reverse('tasks:register')
        )

        self.assertEqual(response.status_code, 200)

    def test_user_can_register(self):
        response = self.client.post(
            reverse('tasks:register'),
            {
                'username': 'newuser',
                'email': 'newuser@example.com',
                'password1': 'T!m3Flow#2026Secure',
                'password2': 'T!m3Flow#2026Secure',
            }
        )

        self.assertRedirects(
            response,
            reverse('tasks:task_list')
        )

        self.assertTrue(
            User.objects.filter(username='newuser').exists()
        )

        self.assertTrue(
            '_auth_user_id' in self.client.session
        )


class TaskOwnershipTests(TestCase):
    """Tests that users can only access their own tasks."""

    def setUp(self):
        self.user1 = User.objects.create_user(
            username='user1',
            password='StrongPass!2026Secure'
        )

        self.user2 = User.objects.create_user(
            username='user2',
            password='StrongPass!2026Secure'
        )

        self.task1 = Task.objects.create(
            owner=self.user1,
            title='User One Task',
            description='Private task belonging to user one',
            priority=Task.Priority.HIGH,
            status=Task.Status.TODO,
        )

        self.task2 = Task.objects.create(
            owner=self.user2,
            title='User Two Task',
            description='Private task belonging to user two',
            priority=Task.Priority.LOW,
            status=Task.Status.COMPLETED,
        )

    def test_user_sees_only_own_tasks(self):
        self.client.force_login(self.user1)

        response = self.client.get(
            reverse('tasks:task_list')
        )

        self.assertEqual(response.status_code, 200)

        self.assertContains(response, 'User One Task')
        self.assertNotContains(response, 'User Two Task')

    def test_user_cannot_edit_another_users_task(self):
        self.client.force_login(self.user1)

        response = self.client.get(
            reverse(
                'tasks:task_update',
                args=[self.task2.pk]
            )
        )

        self.assertEqual(response.status_code, 404)

    def test_user_cannot_delete_another_users_task(self):
        self.client.force_login(self.user1)

        response = self.client.post(
            reverse(
                'tasks:task_delete',
                args=[self.task2.pk]
            )
        )

        self.assertEqual(response.status_code, 404)

        self.assertTrue(
            Task.objects.filter(pk=self.task2.pk).exists()
        )

    def test_user_can_edit_own_task(self):
        self.client.force_login(self.user1)

        response = self.client.post(
            reverse(
                'tasks:task_update',
                args=[self.task1.pk]
            ),
            {
                'title': 'Updated User One Task',
                'description': 'Updated description',
                'priority': Task.Priority.MEDIUM,
                'status': Task.Status.IN_PROGRESS,
                'due_date': '',
            }
        )

        self.assertRedirects(
            response,
            reverse('tasks:task_list')
        )

        self.task1.refresh_from_db()

        self.assertEqual(
            self.task1.title,
            'Updated User One Task'
        )

        self.assertEqual(self.task1.owner, self.user1)

    def test_user_can_delete_own_task(self):
        self.client.force_login(self.user1)

        response = self.client.post(
            reverse(
                'tasks:task_delete',
                args=[self.task1.pk]
            )
        )

        self.assertRedirects(
            response,
            reverse('tasks:task_list')
        )

        self.assertFalse(
            Task.objects.filter(pk=self.task1.pk).exists()
        )

    def test_new_task_is_assigned_to_logged_in_user(self):
        self.client.force_login(self.user1)

        response = self.client.post(
            reverse('tasks:task_create'),
            {
                'title': 'New Personal Task',
                'description': 'Created through the application',
                'priority': Task.Priority.HIGH,
                'status': Task.Status.TODO,
                'due_date': '',
            }
        )

        self.assertRedirects(
            response,
            reverse('tasks:task_list')
        )

        task = Task.objects.get(title='New Personal Task')

        self.assertEqual(task.owner, self.user1)

    def test_owner_field_is_mandatory(self):
        owner_field = Task._meta.get_field('owner')

        self.assertFalse(owner_field.null)
        self.assertFalse(owner_field.blank)

    def test_database_rejects_task_without_owner(self):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Task.objects.create(
                    title='Task Without Owner'
                )


class TaskDashboardTests(TestCase):
    """Tests for dashboard statistics, search and filters."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='dashboarduser',
            password='StrongPass!2026Secure'
        )

        self.other_user = User.objects.create_user(
            username='otheruser',
            password='StrongPass!2026Secure'
        )

        self.client.force_login(self.user)

        Task.objects.create(
            owner=self.user,
            title='Design Website',
            description='Create website homepage',
            priority=Task.Priority.HIGH,
            status=Task.Status.TODO,
        )

        Task.objects.create(
            owner=self.user,
            title='Write Documentation',
            description='Prepare project documentation',
            priority=Task.Priority.MEDIUM,
            status=Task.Status.IN_PROGRESS,
        )

        Task.objects.create(
            owner=self.user,
            title='Complete Testing',
            description='Test all application features',
            priority=Task.Priority.LOW,
            status=Task.Status.COMPLETED,
        )

        Task.objects.create(
            owner=self.other_user,
            title='Other User Private Task',
            priority=Task.Priority.HIGH,
            status=Task.Status.TODO,
        )

    def test_dashboard_loads(self):
        response = self.client.get(
            reverse('tasks:task_list')
        )

        self.assertEqual(response.status_code, 200)

    def test_dashboard_statistics(self):
        response = self.client.get(
            reverse('tasks:task_list')
        )

        self.assertEqual(response.context['total_tasks'], 3)
        self.assertEqual(response.context['completed_tasks'], 1)
        self.assertEqual(response.context['pending_tasks'], 1)
        self.assertEqual(response.context['in_progress_tasks'], 1)

    def test_search_by_task_title(self):
        response = self.client.get(
            reverse('tasks:task_list'),
            {'q': 'Design Website'}
        )

        self.assertContains(response, 'Design Website')
        self.assertNotContains(response, 'Write Documentation')

    def test_search_by_description(self):
        response = self.client.get(
            reverse('tasks:task_list'),
            {'q': 'project documentation'}
        )

        self.assertContains(response, 'Write Documentation')
        self.assertNotContains(response, 'Design Website')

    def test_filter_by_status(self):
        response = self.client.get(
            reverse('tasks:task_list'),
            {'status': Task.Status.COMPLETED}
        )

        self.assertContains(response, 'Complete Testing')
        self.assertNotContains(response, 'Design Website')

    def test_filter_by_priority(self):
        response = self.client.get(
            reverse('tasks:task_list'),
            {'priority': Task.Priority.HIGH}
        )

        self.assertContains(response, 'Design Website')
        self.assertNotContains(response, 'Write Documentation')

    def test_combined_filters(self):
        response = self.client.get(
            reverse('tasks:task_list'),
            {
                'status': Task.Status.TODO,
                'priority': Task.Priority.HIGH,
            }
        )

        self.assertContains(response, 'Design Website')
        self.assertNotContains(response, 'Complete Testing')

    def test_other_users_tasks_not_in_dashboard_statistics(self):
        response = self.client.get(
            reverse('tasks:task_list')
        )

        self.assertEqual(response.context['total_tasks'], 3)

        self.assertNotContains(
            response,
            'Other User Private Task'
        )


class AccessControlTests(TestCase):
    """Tests for anonymous access and Django Admin."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='regularuser',
            password='StrongPass!2026Secure'
        )

        self.task = Task.objects.create(
            owner=self.user,
            title='Protected Task',
        )

    def test_anonymous_user_cannot_access_dashboard(self):
        response = self.client.get(
            reverse('tasks:task_list')
        )

        self.assertRedirects(
            response,
            f"{reverse('login')}?next=/"
        )

    def test_anonymous_user_cannot_create_task(self):
        response = self.client.get(
            reverse('tasks:task_create')
        )

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('login'), response.url)

    def test_anonymous_user_cannot_edit_task(self):
        response = self.client.get(
            reverse(
                'tasks:task_update',
                args=[self.task.pk]
            )
        )

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('login'), response.url)

    def test_anonymous_user_cannot_delete_task(self):
        response = self.client.get(
            reverse(
                'tasks:task_delete',
                args=[self.task.pk]
            )
        )

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('login'), response.url)

    def test_admin_can_view_tasks(self):
        admin_user = User.objects.create_superuser(
            username='siteadmin',
            email='admin@example.com',
            password='Admin!Pass2026Secure'
        )

        self.client.force_login(admin_user)

        response = self.client.get(
            reverse('admin:tasks_task_changelist')
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Protected Task')



class TaskKanbanTests(TestCase):
    """Tests for the Kanban board and secure drag-and-drop status updates."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='kanbanuser',
            password='StrongPass!2026Secure',
        )
        self.other_user = User.objects.create_user(
            username='kanbanother',
            password='StrongPass!2026Secure',
        )
        self.todo_task = Task.objects.create(
            owner=self.user,
            title='Plan Kanban Board',
            status=Task.Status.TODO,
            priority=Task.Priority.HIGH,
        )
        self.progress_task = Task.objects.create(
            owner=self.user,
            title='Build Kanban Board',
            status=Task.Status.IN_PROGRESS,
            priority=Task.Priority.MEDIUM,
        )
        self.completed_task = Task.objects.create(
            owner=self.user,
            title='Test Kanban Board',
            status=Task.Status.COMPLETED,
            priority=Task.Priority.LOW,
        )
        self.private_task = Task.objects.create(
            owner=self.other_user,
            title='Another User Private Task',
            status=Task.Status.TODO,
        )

    def test_kanban_page_requires_login(self):
        response = self.client.get(reverse('tasks:task_kanban'))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('login'), response.url)

    def test_kanban_page_loads_for_authenticated_user(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('tasks:task_kanban'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'tasks/task_kanban.html')
        self.assertEqual(response.context['total_tasks'], 3)

    def test_kanban_only_shows_current_users_tasks(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('tasks:task_kanban'))
        self.assertContains(response, 'Plan Kanban Board')
        self.assertContains(response, 'Build Kanban Board')
        self.assertContains(response, 'Test Kanban Board')
        self.assertNotContains(response, 'Another User Private Task')

    def test_user_can_update_own_task_status(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse('tasks:task_status_update', args=[self.todo_task.pk]),
            {'status': Task.Status.IN_PROGRESS},
        )
        self.assertEqual(response.status_code, 200)
        self.todo_task.refresh_from_db()
        self.assertEqual(self.todo_task.status, Task.Status.IN_PROGRESS)
        self.assertEqual(response.json()['status'], Task.Status.IN_PROGRESS)

    def test_user_cannot_update_another_users_task_status(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse('tasks:task_status_update', args=[self.private_task.pk]),
            {'status': Task.Status.COMPLETED},
        )
        self.assertEqual(response.status_code, 404)
        self.private_task.refresh_from_db()
        self.assertEqual(self.private_task.status, Task.Status.TODO)

    def test_invalid_status_is_rejected(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse('tasks:task_status_update', args=[self.todo_task.pk]),
            {'status': 'archived'},
        )
        self.assertEqual(response.status_code, 400)
        self.todo_task.refresh_from_db()
        self.assertEqual(self.todo_task.status, Task.Status.TODO)

    def test_status_update_requires_post(self):
        self.client.force_login(self.user)
        response = self.client.get(
            reverse('tasks:task_status_update', args=[self.todo_task.pk])
        )
        self.assertEqual(response.status_code, 405)



class TaskCalendarTests(TestCase):
    def setUp(self):
        from datetime import date
        self.user = User.objects.create_user(
            username='calendaruser',
            password='StrongPass!2026Secure',
        )
        self.other_user = User.objects.create_user(
            username='calendarother',
            password='StrongPass!2026Secure',
        )
        self.client.force_login(self.user)
        self.task = Task.objects.create(
            owner=self.user,
            title='Calendar owned task',
            due_date=date(2026, 11, 20),
        )
        Task.objects.create(
            owner=self.other_user,
            title='Private calendar task',
            due_date=date(2026, 11, 20),
        )

    def test_calendar_requires_login(self):
        self.client.logout()
        response = self.client.get(reverse('tasks:task_calendar'))
        self.assertEqual(response.status_code, 302)

    def test_calendar_loads(self):
        response = self.client.get(reverse('tasks:task_calendar'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'tasks/calendar.html')

    def test_calendar_only_includes_current_users_tasks(self):
        response = self.client.get(
            reverse('tasks:task_calendar'),
            {'year': 2026, 'month': 11},
        )
        self.assertContains(response, 'Calendar owned task')
        self.assertNotContains(response, 'Private calendar task')

    def test_calendar_month_navigation_parameters(self):
        response = self.client.get(
            reverse('tasks:task_calendar'),
            {'year': 2026, 'month': 12},
        )
        self.assertEqual(response.context['calendar_month'], 12)
        self.assertEqual(response.context['month_name'], 'December 2026')


class TaskAnalyticsTests(TestCase):
    def setUp(self):
        from datetime import date, timedelta
        from django.utils import timezone
        self.user = User.objects.create_user(
            username='analyticsuser',
            password='StrongPass!2026Secure',
        )
        self.other_user = User.objects.create_user(
            username='analyticsother',
            password='StrongPass!2026Secure',
        )
        self.client.force_login(self.user)
        today = timezone.localdate()

        Task.objects.create(
            owner=self.user,
            title='Analytics completed',
            status=Task.Status.COMPLETED,
            priority=Task.Priority.HIGH,
            due_date=today - timedelta(days=2),
        )
        Task.objects.create(
            owner=self.user,
            title='Analytics overdue',
            status=Task.Status.TODO,
            priority=Task.Priority.MEDIUM,
            due_date=today - timedelta(days=1),
        )
        Task.objects.create(
            owner=self.user,
            title='Analytics active',
            status=Task.Status.IN_PROGRESS,
            priority=Task.Priority.LOW,
        )
        Task.objects.create(
            owner=self.other_user,
            title='Other user analytics task',
            status=Task.Status.TODO,
            due_date=today - timedelta(days=1),
        )

    def test_analytics_requires_login(self):
        self.client.logout()
        response = self.client.get(reverse('tasks:task_analytics'))
        self.assertEqual(response.status_code, 302)

    def test_analytics_page_loads(self):
        response = self.client.get(reverse('tasks:task_analytics'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'tasks/analytics.html')

    def test_analytics_counts_only_current_users_tasks(self):
        response = self.client.get(reverse('tasks:task_analytics'))
        self.assertEqual(response.context['total_tasks'], 3)
        self.assertEqual(response.context['completed_tasks'], 1)
        self.assertEqual(response.context['pending_tasks'], 1)
        self.assertEqual(response.context['in_progress_tasks'], 1)

    def test_analytics_overdue_count_excludes_completed_tasks(self):
        response = self.client.get(reverse('tasks:task_analytics'))
        self.assertEqual(response.context['overdue_tasks'], 1)

    def test_analytics_completion_rate(self):
        response = self.client.get(reverse('tasks:task_analytics'))
        self.assertEqual(response.context['completion_rate'], 33)

    def test_analytics_weekly_activity_has_seven_days(self):
        response = self.client.get(reverse('tasks:task_analytics'))
        self.assertEqual(len(response.context['weekly_activity']), 7)


class AccountSettingsTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='accountuser',
            email='old@example.com',
            password='StrongPass!2026Secure',
        )
        self.client.force_login(self.user)

    def test_account_settings_requires_login(self):
        self.client.logout()
        response = self.client.get(reverse('tasks:profile'))
        self.assertEqual(response.status_code, 302)

    def test_account_settings_page_loads(self):
        response = self.client.get(reverse('tasks:profile'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'tasks/profile.html')

    def test_user_can_update_own_username_and_email(self):
        response = self.client.post(
            reverse('tasks:profile'),
            {
                'username': 'updatedaccount',
                'email': 'updated@example.com',
            },
        )
        self.assertRedirects(response, reverse('tasks:profile'))
        self.user.refresh_from_db()
        self.assertEqual(self.user.username, 'updatedaccount')
        self.assertEqual(self.user.email, 'updated@example.com')

    def test_duplicate_username_is_rejected(self):
        User.objects.create_user(
            username='takenname',
            password='StrongPass!2026Secure',
        )
        response = self.client.post(
            reverse('tasks:profile'),
            {'username': 'takenname', 'email': 'account@example.com'},
        )
        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertEqual(self.user.username, 'accountuser')

    def test_password_change_page_loads(self):
        response = self.client.get(reverse('password_change'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'registration/password_change_form.html')

    def test_user_can_change_password(self):
        response = self.client.post(
            reverse('password_change'),
            {
                'old_password': 'StrongPass!2026Secure',
                'new_password1': 'N3w!TaskFlowPassword2026',
                'new_password2': 'N3w!TaskFlowPassword2026',
            },
        )
        self.assertRedirects(response, reverse('password_change_done'))
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('N3w!TaskFlowPassword2026'))
        self.assertIn('_auth_user_id', self.client.session)

    def test_password_change_done_page_loads(self):
        response = self.client.get(reverse('password_change_done'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'registration/password_change_done.html')
