from django.db import models
from django.core import validators
from django.contrib.auth import get_user_model
import uuid

from registration.validators import UploadedFileValidator

User = get_user_model()


def _generate_team_code():
    team_code = uuid.uuid4().hex[:5].upper()
    while Team.objects.filter(team_code=team_code).exists():
        team_code = uuid.uuid4().hex[:5].upper()
    return team_code


class Team(models.Model):
    team_code = models.CharField(max_length=5, default=_generate_team_code, null=False)

    created_at = models.DateTimeField(auto_now_add=True, null=False)
    updated_at = models.DateTimeField(auto_now=True, null=False)

    MAX_MEMBERS = 4

    def __str__(self):
        return self.team_code


class Application(models.Model):
    PRONOUN_CHOICES = [
        (None, ""),
        ("he-him", "he/him"),
        ("she-her", "she/her"),
        ("they-them", "they/them"),
        ("other", "other"),
        ("no-answer", "prefer not to answer"),
    ]

    ETHNICITY_CHOICES = [
        (None, ""),
        ("american-native", "American Indian or Alaskan Native"),
        ("asian-pacific-islander", "Asian / Pacific Islander"),
        ("black-african-american", "Black or African American"),
        ("hispanic", "Hispanic"),
        ("caucasian", "White / Caucasian"),
        ("other", "Multiple ethnicity / Other"),
        ("no-answer", "Prefer not to answer"),
    ]

    STUDY_LEVEL_CHOICES = [
        (None, ""),
        ("less-than-secondary", "Less than Secondary / High School"),
        ("secondary", "Secondary / High School"),
        (
            "undergraduate-2-year",
            "Undergraduate University (2 year - community college or similar)",
        ),
        ("undergraduate-3-year", "Undergraduate University (3+ year)"),
        ("graduate", "Graduate University (Masters, Professional, Doctoral, etc)"),
        ("code-school", "Code School / Bootcamp"),
        ("vocational", "Other Vocational / Trade Program or Apprenticeship"),
        ("post-doctorate", "Post Doctorate"),
        ("other", "Other"),
        ("not-a-student", "I’m not currently a student"),
        ("no-answer", "Prefer not to answer"),
    ]

    AGE_CHOICES = [
        (None, ""),
        (18, "18"),
        (19, "19"),
        (20, "20"),
        (21, "21"),
        (22, "22"),
        (23, "22+"),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, null=False)
    team = models.ForeignKey(
        Team, related_name="applications", on_delete=models.CASCADE, null=False
    )

    # User Submitted Fields
    age = models.PositiveIntegerField(choices=AGE_CHOICES, null=False)
    under_age = models.BooleanField(null=False, default=False)
    pronouns = models.CharField(
        max_length=50, choices=PRONOUN_CHOICES, null=False, default=""
    )
    ethnicity = models.CharField(max_length=50, choices=ETHNICITY_CHOICES, null=False)
    phone_number = models.CharField(
        max_length=20,
        null=False,
        validators=[
            validators.RegexValidator(
                r"^(?:\+\d{1,3})?\s?\(?\d{3}\)?[\s-]?\d{3}[\s-]?\d{4}$",
                message="Enter a valid phone number.",
            )
        ],
    )
    city = models.CharField(max_length=255, null=False)
    country = models.CharField(max_length=255, null=False)
    school = models.CharField(max_length=255, null=False,)
    study_level = models.CharField(
        max_length=50,
        help_text="Level of Study",
        choices=STUDY_LEVEL_CHOICES,
        null=False,
    )
    graduation_year = models.IntegerField(
        null=False,
        validators=[
            validators.MinValueValidator(
                2000, message="Enter a realistic graduation year."
            ),
            validators.MaxValueValidator(
                2030, message="Enter a realistic graduation year."
            ),
        ],
    )
    program = models.CharField(
        max_length=255, help_text="Program or Major", null=False, default=""
    )
    resume = models.FileField(
        upload_to="applications/resumes/",
        validators=[
            UploadedFileValidator(
                content_types=["application/pdf"], max_upload_size=20 * 1024 * 1024
            )
        ],
        null=False,
    )
    linkedin = models.URLField(
        max_length=200, help_text="LinkedIn Profile (Optional)", null=True, blank=True
    )
    github = models.URLField(
        max_length=200, help_text="Github Profile (Optional)", null=True, blank=True
    )
    devpost = models.URLField(
        max_length=200, help_text="Devpost Profile (Optional)", null=True, blank=True
    )
    why_participate = models.TextField(
        null=False,
        help_text="Why do you want to participate in NewHacks?",
        max_length=1000,
    )
    what_technical_experience = models.TextField(
        null=False,
        help_text="What is your technical experience with software?",
        max_length=1000,
    )
    what_past_experience = models.TextField(
        null=False,
        help_text="If you’ve been to a hackathon, briefly tell us your experience. If not, describe what you expect to see and experience.",
        max_length=1000,
    )
    conduct_agree = models.BooleanField(
        help_text="I have read and agree to the "
        '<a href="https://static.mlh.io/docs/mlh-code-of-conduct.pdf" rel="noopener noreferrer" target="_blank">MLH code of conduct</a>.',
        blank=False,
        null=False,
        default=False,
    )
    logistics_agree = models.BooleanField(
        help_text="I authorize you to share my application/registration information with Major League Hacking"
        " for event administration, ranking, and MLH administration in-line with the "
        '<a href="https://mlh.io/privacy" rel="noopener noreferrer" target="_blank">MLH Privacy Policy</a>. '
        "I further agree to the terms of both the "
        '<a href="https://github.com/MLH/mlh-policies/blob/main/contest-terms.md" rel="noopener noreferrer" target="_blank">MLH Contest Terms and Conditions</a>'
        " and the "
        '<a href="https://mlh.io/privacy" rel="noopener noreferrer" target="_blank">MLH Privacy Policy.</a>',
        blank=False,
        null=False,
        default=False,
    )

    email_agree = models.BooleanField(
        help_text="I authorize MLH to send me occasional emails about relevant events, career opportunities, and community announcements.",
        blank=True,
        null=True,
        default=False,
    )

    resume_sharing = models.BooleanField(
        help_text="I consent to IEEE UofT sharing my resume with event sponsors.",
        blank=True,
        null=True,
        default=False,
    )
    rsvp = models.BooleanField(null=True)

    created_at = models.DateTimeField(auto_now_add=True, null=False)
    updated_at = models.DateTimeField(auto_now=True, null=False)

    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name}"
