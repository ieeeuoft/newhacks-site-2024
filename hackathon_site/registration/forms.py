from dateutil.relativedelta import relativedelta
import re

from captcha.fields import ReCaptchaField
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.utils.translation import gettext_lazy as _
from django_registration import validators
from django.conf import settings

from hackathon_site.utils import is_registration_open
from registration.models import Application, Team, User
from registration.widgets import MaterialFileInput


class SignUpForm(UserCreationForm):
    """
    Form for registering a new user account.

    Similar to django_registration's ``RegistrationForm``, but doesn't
    require a username field. Instead, email is a required field, and
    username is automatically set to be the email. This is ultimately
    simpler than creating a custom user model to use email as username.
    """

    captcha = ReCaptchaField(label="")
    error_css_class = "invalid"

    class Meta(UserCreationForm.Meta):
        fields = [
            User.get_email_field_name(),
            "first_name",
            "last_name",
            "password1",
            "password2",
        ]
        labels = {
            User.get_email_field_name(): _("Email"),
            "first_name": _("First Name"),
            "last_name": _("Last Name"),
            "password1": _("Password"),
            "password2": _("Confirm Password"),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        email_field = User.get_email_field_name()
        self.fields[email_field].validators.extend(
            (
                validators.HTML5EmailValidator(),
                validators.validate_confusables_email,
                validators.CaseInsensitiveUnique(
                    User, email_field, "This email is unavailable"
                ),
            )
        )
        self.label_suffix = ""

        # This overrides the default labels set by UserCreationForm
        for field, label in self._meta.labels.items():
            self.fields[field].label = label

        for field in self._meta.fields:
            self.fields[field].required = True

    def clean_email(self):
        return self.cleaned_data["email"].lower()

    def clean_first_name(self):
        if not bool(re.search("^[a-zA-Z0-9\s-]*$", self.cleaned_data["first_name"])):
            raise forms.ValidationError(
                _(
                    f"This doesn't seem like a name, please enter a valid name (no special characters)"
                ),
                code="invalid_first_name",
            )

        if len(self.cleaned_data["first_name"]) > 30:
            raise forms.ValidationError(
                _(f"This input seems too long to be a name, please enter a valid name"),
                code="first_name_too_long",
            )
        return self.cleaned_data["first_name"]

    def clean_last_name(self):
        if not bool(re.search("^[a-zA-Z0-9\s-]*$", self.cleaned_data["last_name"])):
            raise forms.ValidationError(
                _(
                    f"This doesn't seem like a name, please enter a valid name (no special characters)"
                ),
                code="invalid_last_name",
            )

        if len(self.cleaned_data["last_name"]) > 30:
            raise forms.ValidationError(
                _(f"This input seems too long to be a name, please enter a valid name"),
                code="last_name_too_long",
            )
        return self.cleaned_data["last_name"]

    def save(self, commit=True):
        """
        Set the user's username to their email when saving

        This is much simpler than the alternative of creating a
        custom user model without a username field, but a caveat
        nonetheless.
        """

        user = super().save(commit=False)
        user.username = self.cleaned_data["email"]
        if commit:
            user.save()
        return user


class ApplicationForm(forms.ModelForm):
    error_css_class = "invalid"

    class Meta:
        model = Application
        fields = [
            "age",
            "pronouns",
            "free_response_pronouns",
            "gender",
            "free_response_gender",
            # "ethnicity",
            "phone_number",
            "city",
            "country",
            "tshirt_size",
            "dietary_restrictions",
            "free_response_dietary_restrictions",
            "under_represented_group",
            "sexual_identity",
            "free_response_sexual_identity",
            "highest_formal_education",
            "free_response_highest_formal_education",
            "school",
            "study_level",
            "graduation_year",
            "program",
            "resume",
            "linkedin",
            "github",
            "devpost",
            "how_many_hackathons",
            "past_hackathon_info",
            "what_past_experience",
            "why_participate",
            "what_technical_experience",
            "what_role_in_team_setting",
            "discovery_method",
            "conduct_agree",
            "logistics_agree",
            "email_agree",
            "resume_sharing",
        ]
        widgets = {
            "school": forms.Select(
                # Choices will be populated by select2
                attrs={"class": "select2-school-select"},
                choices=((None, ""),),
            ),
            "resume": MaterialFileInput(),
            "free_response_pronouns": forms.Textarea(
                attrs={"class": "materialize-textarea", "data-length": 200}
            ),
            "free_response_gender": forms.Textarea(
                attrs={"class": "materialize-textarea", "data-length": 200}
            ),
            "free_response_sexual_identity": forms.Textarea(
                attrs={"class": "materialize-textarea", "data-length": 200}
            ),
            "free_response_dietary_restrictions": forms.Textarea(
                attrs={"class": "materialize-textarea", "data-length": 200}
            ),
            "free_response_highest_formal_education": forms.Textarea(
                attrs={"class": "materialize-textarea", "data-length": 200}
            ),
            "past_hackathon_info": forms.Textarea(
                attrs={
                    "class": "materialize-textarea",
                    "placeholder": "Insert past hackathon description here...",
                    "data-length": 1000,
                }
            ),
            "what_past_experience": forms.Textarea(
                attrs={
                    "class": "materialize-textarea",
                    "placeholder": "Insert answer here...",
                    "data-length": 1000,
                    "style": "padding-top: 38px;",
                }
            ),
            "why_participate": forms.Textarea(
                attrs={
                    "class": "materialize-textarea",
                    "placeholder": "I want to participate in NewHacks because...",
                    "data-length": 1000,
                }
            ),
            "what_technical_experience": forms.Textarea(
                attrs={
                    "class": "materialize-textarea",
                    "placeholder": "My technical experience with software and hardware are...",
                    "data-length": 1000,
                }
            ),
            "what_role_in_team_setting": forms.Textarea(
                attrs={
                    "class": "materialize-textarea",
                    "placeholder": "I take on the role of...",
                    "data-length": 1000,
                }
            ),
            "phone_number": forms.TextInput(attrs={"placeholder": "+1 (123) 456-7890"}),
            "graduation_year": forms.NumberInput(attrs={"placeholder": 2023}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user")
        super().__init__(*args, **kwargs)
        self.label_suffix = ""
        self.fields["conduct_agree"].required = True
        self.fields["logistics_agree"].required = True

    def clean(self):
        if not is_registration_open():
            raise forms.ValidationError(
                _("Registration has closed."), code="registration_closed"
            )

        cleaned_data = super().clean()
        if hasattr(self.user, "application"):
            raise forms.ValidationError(
                _("User has already submitted an application."), code="invalid"
            )
        self.clean_age()
        self.handle_free_response_pronouns()
        self.handle_free_response_gender()
        self.handle_free_response_sexual_identity()
        self.handle_free_response_dietary_restrictions()
        self.handle_highest_formal_education()
        return cleaned_data

    def clean_age(self):
        user_age = self.cleaned_data["age"]
        # Check if the age is "22+"
        if user_age == "22+":
            return user_age
        if user_age < settings.MINIMUM_AGE:
            raise forms.ValidationError(
                _(f"You must be {settings.MINIMUM_AGE} to participate."),
                code="user_is_too_young_to_participate",
            )
        return user_age

    def handle_free_response_pronouns(self):
        user_pronouns = self.cleaned_data["pronouns"]
        user_free_response_pronouns = self.cleaned_data["free_response_pronouns"]
        if user_pronouns == "other" and not user_free_response_pronouns:
            raise forms.ValidationError(
                _(
                    "Since you've selected 'Other' for pronouns, please state what pronouns you go by."
                ),
                code="free_response_pronouns",
            )

    def handle_free_response_gender(self):
        user_gender = self.cleaned_data["gender"]
        user_free_response_gender = self.cleaned_data["free_response_gender"]
        if user_gender == "prefer-to-self-describe" and not user_free_response_gender:
            raise forms.ValidationError(
                _(
                    "Since you've selected 'Prefer to Self Describe' for gender, please state how you would like to be addressed"
                ),
                code="free_response_gender",
            )

    def handle_free_response_dietary_restrictions(self):
        user_dietary_restrictions = self.cleaned_data["dietary_restrictions"]
        user_free_response_dietary_restrictions = self.cleaned_data[
            "free_response_dietary_restrictions"
        ]
        if (
            user_dietary_restrictions == "allergies"
            or user_dietary_restrictions == "other"
        ) and not user_free_response_dietary_restrictions:
            raise forms.ValidationError(
                _("Please provide more information about your dietary restrictions."),
                code="free_response_dietary_restrictions",
            )

    def handle_free_response_sexual_identity(self):
        user_sexual_identity = self.cleaned_data["sexual_identity"]
        user_free_response_sexual_identity = self.cleaned_data[
            "free_response_sexual_identity"
        ]
        if (
            user_sexual_identity == "different-identity"
            and not user_free_response_sexual_identity
        ):
            raise forms.ValidationError(
                _(
                    "You've selected 'Different Identity', please state how you would like to identify yourself"
                ),
                code="free_response_sexual_identity",
            )

    def handle_highest_formal_education(self):
        user_highest_formal_education = self.cleaned_data["highest_formal_education"]
        user_free_response_highest_formal_education = self.cleaned_data[
            "free_response_highest_formal_education"
        ]
        if (
            user_highest_formal_education == "other"
            and not user_free_response_highest_formal_education
        ):
            raise forms.ValidationError(
                _(
                    "You've selected 'Other' for highest formal education, please elaborate in the corresponding field."
                ),
                code="free_response_highest_formal_education",
            )

    def save(self, commit=True):
        self.instance = super().save(commit=False)
        team = Team.objects.create()

        self.instance.user = self.user
        self.instance.team = team
        self.instance.phone_number = re.sub("[^0-9]", "", self.instance.phone_number)

        if commit:
            self.instance.save()
            self.save_m2m()

        return self.instance


class JoinTeamForm(forms.Form):
    team_code = forms.CharField()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.label_suffix = ""
        self.error_css_class = "invalid"

    def clean(self):
        if not is_registration_open():
            raise forms.ValidationError(
                _("You cannot change teams after registration has closed."),
                code="registration_closed",
            )

        return super().clean()

    def clean_team_code(self):
        team_code = self.cleaned_data["team_code"]

        try:
            team = Team.objects.get(team_code=team_code)
        except Team.DoesNotExist:
            raise forms.ValidationError(_(f"Team {team_code} does not exist."))

        if team.applications.count() >= Team.MAX_MEMBERS:
            raise forms.ValidationError(_(f"Team {team_code} is full."))

        return team_code

class SignInForm(forms.Form):
    email = forms.EmailField()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.label_suffix = ""
        self.error_css_class = "invalid"

    def clean(self):
        if not is_hackathon_happening():
            raise forms.ValidationError(
                _("You cannot sign in outside of the hackathon period."),
                code="invalid_sign_in_time",
            )

        return super().clean()

    def clean_email(self):
        email = self.cleaned_data["email"]

        try:
            user = User.objects.get(email__exact=email)
            application = Application.objects.get(user__exact=user)
            review = Review.objects.get(application__exact=application)
            if review.status == "Accepted":
                if settings.RSVP and application.rsvp is None:
                    raise forms.ValidationError(
                        _(f"User {email} has not RSVP'd to the hackathon")
                    )
            else:
                raise forms.ValidationError(
                    _(
                        f"User {email} has not been Accepted to attend {settings.HACKATHON_NAME}"
                    )
                )
        except User.DoesNotExist:
            raise forms.ValidationError(_(f"User {email} does not exist."))
        except Application.DoesNotExist:
            raise forms.ValidationError(
                _(f"User {email} has not applied to {settings.HACKATHON_NAME}")
            )
        except Exception as e:
            raise e

        return email