import re
from unittest.mock import patch
from datetime import datetime, timedelta, date

from django.core import mail
from django.contrib.auth.models import Group
from django.conf import settings
from django.test import TestCase
from django.urls import reverse
from rest_framework import status

from event.models import Profile, User, Team as EventTeam
from hackathon_site.tests import SetupUserMixin
from registration.models import Team as RegistrationTeam, Application

from event.serializers import (
    UserSerializer,
    GroupSerializer,
    ProfileSerializer,
    CurrentProfileSerializer,
    ProfileInUserSerializer,
    ProfileInTeamSerializer,
    UserInProfileSerializer,
    UserReviewStatusSerializer,
    ProfileCreateResponseSerializer,
)
from review.models import Review


class ProfileTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="foo@bar.com",
            password="foobar123",
            first_name="Foo",
            last_name="Bar",
        )

    def test_creates_profile_with_provided_team(self):
        team = EventTeam.objects.create()
        profile = Profile.objects.create(user=self.user, team=team)
        self.assertEqual(EventTeam.objects.count(), 1)
        self.assertEqual(profile.team, team)

    def test_creates_team_if_not_provided(self):
        profile = Profile.objects.create(user=self.user)
        self.assertEqual(EventTeam.objects.count(), 1)
        self.assertEqual(EventTeam.objects.first(), profile.team)


class ProfileSignalTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="foo@bar.com",
            password="foobar123",
            first_name="Foo",
            last_name="Bar",
        )
        self.team = EventTeam.objects.create()
        self.profile = Profile.objects.create(user=self.user, team=self.team)

    def test_remove_team_when_empty(self):
        self.profile.delete()
        self.assertEqual(EventTeam.objects.count(), 0)

    def test_cascade_on_delete_user(self):
        self.user.delete()
        self.assertEqual(EventTeam.objects.count(), 0)

    def test_keep_team_when_not_empty(self):
        second_user = User.objects.create(
            username="bar@bar.com",
            password="foobar123",
            first_name="Foo",
            last_name="Bar",
        )
        second_profile = Profile.objects.create(user=second_user, team=self.team)
        self.profile.delete()
        self.assertEqual(EventTeam.objects.count(), 1)
        second_profile.delete()
        self.assertEqual(EventTeam.objects.count(), 0)


class IndexViewTestCase(SetupUserMixin, TestCase):
    """
    Tests for the landing page template.

    We test for correct rendering and rendering of Logout/Login buttons
    """

    def setUp(self):
        super().setUp()
        self.view = reverse("event:index")

    def test_index_view(self):
        response = self.client.get(self.view)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertContains(response, "Login")
        self.assertContains(response, "Apply")
        self.assertContains(response, reverse("registration:signup"))

    def test_logout_button_renders_when_logged_in(self):
        self._login()
        response = self.client.get(self.view)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertContains(response, "Logout")

    def test_links_to_application_when_not_applied_and_registration_open(self):
        self._login()
        response = self.client.get(self.view)
        self.assertContains(response, "Continue Application")
        self.assertContains(response, reverse("registration:application"))

    @patch("event.views.is_registration_open")
    def test_links_to_dashboard_when_not_applied_and_registration_closed(
        self, mock_is_registration_open
    ):
        mock_is_registration_open.return_value = False
        self._login()
        response = self.client.get(self.view)
        self.assertContains(response, "Go to Dashboard")
        self.assertContains(response, reverse("event:dashboard"))

    def test_links_to_dashboard_when_applied(self):
        self._login()
        self._apply()
        response = self.client.get(self.view)
        self.assertContains(response, "Go to Dashboard")
        self.assertContains(response, reverse("event:dashboard"))

    @patch("event.views.is_registration_open")
    def test_no_apply_button_when_registration_closed(self, mock_is_registration_open):
        mock_is_registration_open.return_value = False
        response = self.client.get(self.view)
        self.assertNotContains(response, reverse("registration:signup"))


class DashboardTestCase(SetupUserMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.view = reverse("event:dashboard")

    def test_redirects_to_login(self):
        """
        Redirects to the login page when not logged in
        """
        response = self.client.get(self.view)
        self.assertRedirects(response, f"{reverse('event:login')}?next={self.view}")

    def test_renders_when_logged_in(self):
        """
        Renders the dashboard when logged in

        Once the dashboard is fully implemented, this test should
        be complemented with a whole suite of tests depending on
        the user's progress through the application, etc.
        """
        self._login()
        response = self.client.get(self.view)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertContains(response, "Dashboard")

    def test_dashboard_when_not_applied(self):
        """
        Test the dashboard when the user has not applied

        It should:
        - Link to the application page
        - Have a note about applying before forming a team
        """
        self._login()
        response = self.client.get(self.view)
        self.assertContains(response, "Complete your application")
        self.assertContains(response, "Application Incomplete")
        self.assertContains(response, reverse("registration:application"))

    def test_dashboard_when_applied(self):
        """
        Test the dashboard after the user has applied
        """
        self._login()
        self._apply()
        response = self.client.get(self.view)
        self.assertNotContains(response, reverse("registration:application"))
        self.assertContains(response, "Application Complete")

    def test_dashboard_when_application_reviewed_but_decision_not_sent(self):
        """
        Test the dashboard after the user's application has been reviewed but a decision
        has not been sent to the user yet. The user's dashboard should display the same
        as when they have just completed their application
        """
        self._login()
        self._apply()
        self._review(decision_sent_date=None)

        response = self.client.get(self.view)
        self.assertNotContains(response, reverse("registration:application"))
        self.assertNotContains(
            response, "You must complete your application before you can form a team"
        )
        self.assertContains(response, "Application Complete")

        # Can't join teams anymore because reviewed
        self.assertNotContains(response, "Join a different team")

    def test_dashboard_when_waitlisted(self):
        """
        Test the dashboard when user has been waitlisted
        """
        self._login()
        self._apply()
        self._review(status="Waitlisted")
        response = self.client.get(self.view)

        self.assertContains(response, "Waitlisted")
        self.assertContains(
            response, f"You've been waitlisted for {settings.HACKATHON_NAME}"
        )

        # Can't join teams anymore because reviewed
        self.assertNotContains(response, "Join a different team")

    def test_dashboard_when_rejected(self):
        """
        Test the dashboard when user has been rejected
        """
        self._login()
        self._apply()
        self._review(status="Rejected")
        response = self.client.get(self.view)

        self.assertContains(response, "Rejected")
        self.assertContains(
            response, f"You've been rejected from {settings.HACKATHON_NAME}"
        )

        # Can't join teams anymore because reviewed
        self.assertNotContains(response, "Join a different team")

    @patch("event.views.is_registration_open")
    def test_when_not_applied_and_applications_closed(self, mock_is_registration_open):
        mock_is_registration_open.return_value = False
        self._login()
        response = self.client.get(self.view)
        self.assertContains(response, "Applications have closed")
        self.assertNotContains(response, "Complete your application")
        self.assertNotContains(response, "Apply as a team")

    @patch("event.views.is_registration_open")
    def test_shows_submitted_application_after_applications_closed(
        self, mock_is_registration_open
    ):
        mock_is_registration_open.return_value = False
        self._login()
        self._apply()
        response = self.client.get(self.view)
        self.assertContains(response, "Your application has been submitted!")
        self.assertNotContains(response, "Spots remaining on your team")


class LogInViewTestCase(SetupUserMixin, TestCase):
    """
    Tests for the login template.

    This view uses django.contrib.auth.forms.AuthenticationForm, so no direct
    form testing is required.

    Ideally, selenium should be used for a full test of the view UI.
    For practicality reasons, tests for templates with forms are limited to
    POSTing raw data at this time.
    """

    def setUp(self):
        super().setUp()
        self.view = reverse("event:login")

    def test_login_get(self):
        response = self.client.get(self.view)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_submit_login_missing_username_and_password(self):
        response = self.client.post(self.view, {"username": "", "password": ""})
        self.assertContains(response, "This field is required", count=2)

    def test_submit_login_invalid_credentials(self):
        response = self.client.post(
            self.view, {"username": "fake@email.com", "password": "abc123"}
        )
        self.assertContains(response, "Please enter a correct username and password")

    def test_submit_login_valid_credentials(self):
        response = self.client.post(
            self.view, {"username": self.user.username, "password": self.password}
        )
        self.assertEqual(response.url, settings.LOGIN_REDIRECT_URL)

    def test_submit_login_uppercase_username(self):
        response = self.client.post(
            self.view,
            {"username": self.user.username.upper(), "password": self.password},
        )
        self.assertEqual(response.url, settings.LOGIN_REDIRECT_URL)


class LogOutViewTestCase(SetupUserMixin, TestCase):
    """
    Tests for the logout template. We simply redirect to the homepage.

    This view uses django.contrib.auth.views.LogoutView, so no logic testing
    is required.
    """

    def setUp(self):
        super().setUp()
        self.view = reverse("event:logout")
        self._login()

    def test_logout_get(self):
        response = self.client.get(self.view)
        self.assertRedirects(response, settings.LOGOUT_REDIRECT_URL)


class PasswordChangeTestCase(SetupUserMixin, TestCase):
    """
    Tests for the password change template if already logged in.

    This view uses django.contrib.auth.views.PasswordChangeView and
    django.contrib.auth.views.PasswordChangeDoneView so no logic testing
    is required.
    """

    def setUp(self):
        super().setUp()
        self.view = reverse("event:change_password")
        self._login()

    def test_change_password_get(self):
        response = self.client.get(self.view)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_valid_submit_redirect(self):
        data = {
            "old_password": self.password,
            "new_password1": "abcdef456",
            "new_password2": "abcdef456",
        }
        response = self.client.post(self.view, data)
        self.assertRedirects(response, reverse("event:change_password_done"))
        redirected_response = response.client.get(response.url)
        self.assertContains(
            redirected_response, "Your password was changed successfully"
        )


class PasswordResetTestCase(SetupUserMixin, TestCase):
    """
    Tests for the password reset template (reset password without login).

    This view uses django.contrib.auth.views.PasswordResetView,
    django.contrib.auth.views.PasswordResetDoneView,
    django.contrib.auth.views.PasswordResetConfirmView, and
    django.contrib.auth.views.PasswordResetCompleteView, so no logic testing
    is required.
    """

    def setUp(self):
        super().setUp()
        self.view_request_reset = reverse("event:reset_password")

    def test_reset_password_get(self):
        response = self.client.get(self.view_request_reset)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_reset_password_valid_submit_redirect(self):
        data = {"email": self.user.email}
        response = self.client.post(self.view_request_reset, data)
        self.assertRedirects(response, reverse("event:reset_password_done"))
        redirected_response = response.client.get(response.url)
        self.assertContains(redirected_response, "Password reset sent")

        self.assertIn(settings.HACKATHON_NAME, mail.outbox[0].subject)

    def test_reset_password_confirm_get(self):
        data = {"email": self.user.email}
        self.client.post(self.view_request_reset, data)

        clean = re.compile("<.*?>")
        clean_mail_body = re.sub(clean, "", mail.outbox[0].body)

        reset_link = [
            line for line in clean_mail_body.split("\n") if "http://testserver/" in line
        ][0]

        uid_hash = reset_link.split("/")[-3]

        response = self.client.get(reset_link)
        self.assertRedirects(
            response,
            reverse("event:reset_password_confirm", args=[uid_hash, "set-password"]),
        )
        redirected_response = response.client.get(response.url)
        self.assertContains(redirected_response, "Reset Password")

    def test_reset_password_confirm_valid_submit_redirect(self):
        user_data = {"email": self.user.email}
        self.client.post(self.view_request_reset, user_data)

        clean = re.compile("<.*?>")
        clean_mail_body = re.sub(clean, "", mail.outbox[0].body)

        reset_link = [
            line for line in clean_mail_body.split("\n") if "http://testserver/" in line
        ][0]

        response = self.client.get(reset_link)
        response.client.get(response.url)
        new_password_data = {"new_password1": "abcdabcd", "new_password2": "abcdabcd"}

        submitted_response = self.client.post(response.url, new_password_data)

        self.assertRedirects(
            submitted_response, reverse("event:reset_password_complete")
        )
        redirected_response = self.client.get(submitted_response.url)
        self.assertContains(
            redirected_response, "Your password has been successfully reset"
        )


class UserSerializerTestCase(TestCase):
    def test_serializer(self):
        team = EventTeam.objects.create()
        group = Group.objects.create(name="Test")
        user = User.objects.create()
        user.groups.add(group)

        Profile.objects.create(
            user=user, team=team,
        )

        user_serialized = UserSerializer(user).data
        profile_serialized = ProfileInUserSerializer(user.profile).data
        group_serialized = GroupSerializer(user.groups, many=True).data

        user_expected = {
            "id": user.id,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email": user.email,
            "profile": profile_serialized,
            "groups": group_serialized,
        }

        self.assertEqual(user_expected, user_serialized)


class UserInProfileSerializerTestCase(TestCase):
    def test_serializer(self):
        team = EventTeam.objects.create()

        user = User.objects.create()

        Profile.objects.create(
            user=user, team=team,
        )

        user_serialized = UserInProfileSerializer(user).data

        user_expected = {
            "id": user.id,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email": user.email,
        }

        self.assertEqual(user_expected, user_serialized)


class GroupSerializerTestCase(TestCase):
    def test_serializer(self):
        group = Group.objects.create(name="Test")
        group_serialized = GroupSerializer(group).data
        group_expected = {
            "id": group.id,
            "name": group.name,
        }
        self.assertEqual(group_expected, group_serialized)


class ProfileSerializerTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="foo@bar.com",
            password="foobar123",
            first_name="Foo",
            last_name="Bar",
        )

    def test_serializer(self):
        team = EventTeam.objects.create()

        profile = Profile.objects.create(
            user=self.user, team=team, phone_number="1234567890"
        )
        profile_serialized = ProfileSerializer(profile).data
        profile_expected = {
            "id": profile.id,
            "id_provided": profile.id_provided,
            "attended": profile.attended,
            "acknowledge_rules": profile.acknowledge_rules,
            "e_signature": profile.e_signature,
            "team": team.id,
            "phone_number": profile.phone_number,
        }
        self.assertEqual(profile_expected, profile_serialized)


class CurrentProfileSerializerTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="foo@bar.com",
            password="foobar123",
            first_name="Foo",
            last_name="Bar",
        )

    def test_readonly_serializer_fields(self):
        self.assertEqual(
            CurrentProfileSerializer.Meta.read_only_fields,
            ("id", "team", "id_provided", "attended", "phone_number"),
        )


class CreateProfileSerializerTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="foo@bar.com",
            password="foobar123",
            first_name="Foo",
            last_name="Bar",
        )
        self.team = RegistrationTeam.objects.create()

        application_data = {
            "age": 18,
            "pronouns": "no-answer",
            "ethnicity": "no-answer",
            "phone_number": "1234567890",
            "city": "Toronto",
            "country": "Canada",
            "school": "UofT",
            "study_level": "other",
            "graduation_year": 2020,
            "program": "Engineering",
            "resume": "uploads/resumes/my_resume.pdf",
            "why_participate": "hi",
            "what_technical_experience": "there",
            "what_past_experience": "foo",
            "conduct_agree": True,
            "email_agree": True,
            "logistics_agree": True,
            "resume_sharing": True,
        }
        self.application = Application.objects.create(
            user=self.user, team=self.team, **application_data
        )
        self.profile = Profile.objects.create(user=self.user)

    def test_serializer(self):
        profile_create_response = {
            "id_provided": self.profile.id_provided,
            "attended": self.profile.attended,
            "acknowledge_rules": self.profile.acknowledge_rules,
            "e_signature": self.profile.e_signature,
            "team": self.profile.team.team_code,
            "phone_number": self.application.phone_number,
        }
        serialized_profile = ProfileCreateResponseSerializer(
            data=profile_create_response
        )
        self.assertEqual(serialized_profile.is_valid(), True)
        self.assertEqual(profile_create_response, serialized_profile.data)


class ProfileInUserSerializerTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="foo@bar.com",
            password="foobar123",
            first_name="Foo",
            last_name="Bar",
        )

    def test_serializer(self):
        team = EventTeam.objects.create()

        profile = Profile.objects.create(
            user=self.user, team=team, phone_number="1234567890"
        )
        profile_serialized = ProfileInUserSerializer(profile).data

        profile_expected = {
            "id": profile.id,
            "id_provided": profile.id_provided,
            "attended": profile.attended,
            "acknowledge_rules": profile.acknowledge_rules,
            "e_signature": profile.e_signature,
            "user": UserInProfileSerializer(profile.user).data,
            "phone_number": profile.phone_number,
        }

        self.assertEqual(profile_expected, profile_serialized)


class ProfileInTeamSerilializerTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="foo@bar.com",
            password="foobar123",
            first_name="Foo",
            last_name="Bar",
        )

    def test_serializer(self):
        team = EventTeam.objects.create()

        profile = Profile.objects.create(
            user=self.user, team=team, phone_number="1234567890"
        )
        profile_serialized = ProfileInTeamSerializer(profile).data

        profile_expected = {
            "id": profile.id,
            "id_provided": profile.id_provided,
            "attended": profile.attended,
            "acknowledge_rules": profile.acknowledge_rules,
            "e_signature": profile.e_signature,
            "user": UserInProfileSerializer(profile.user).data,
            "phone_number": profile.phone_number,
        }

        self.assertEqual(profile_expected, profile_serialized)


class UserReviewStatusSerializerTestCase(SetupUserMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.application = self._apply_as_user(self.user)

    def test_serializer(self):
        self._review()
        user_serialized = UserReviewStatusSerializer(self.user).data

        user_expected = {
            "id": self.user.id,
            "first_name": self.user.first_name,
            "last_name": self.user.last_name,
            "email": self.user.email,
            "review_status": self.review.status,
        }

        self.assertEqual(user_expected, user_serialized)

    def test_serializer_no_review(self):
        user_serialized = UserReviewStatusSerializer(self.user).data

        user_expected = {
            "id": self.user.id,
            "first_name": self.user.first_name,
            "last_name": self.user.last_name,
            "email": self.user.email,
            "review_status": "None",
        }

        self.assertEqual(user_expected, user_serialized)
