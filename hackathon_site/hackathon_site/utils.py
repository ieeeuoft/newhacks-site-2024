from datetime import datetime

from django.conf import settings


def is_registration_open():
    """
    Determine whether registration is currently open.

    Note: Registration being open refers to a user being able to simply create an account.
    """
    if settings.IN_TESTING:
        # So tests don't rely on the date, default to true
        return True

    # datetime.now() returns the system native time, so this assumes that the system timezone
    # is configured to match TIME_ZONE. We then make the datetime object timezone-aware.
    now = datetime.now().replace(tzinfo=settings.TZ_INFO)
    return settings.REGISTRATION_OPEN_DATE <= now < settings.REGISTRATION_CLOSE_DATE


def is_application_open():
    """
    Determine whether applications are currently open.

    Note: Applications being open refers to a user's ability to fill out and
    submit the hackathon application
    The application time window is defined as being between the application open
    date (inclusive), and when registration closes (exclusive)
    """
    if settings.IN_TESTING:
        # So tests don't rely on the date, default to true
        return True

    # datetime.now() returns the system native time, so this assumes that the system timezone
    # is configured to match TIME_ZONE. We then make the datetime object timezone-aware.
    now = datetime.now().replace(tzinfo=settings.TZ_INFO)
    return settings.APPLICATION_OPEN_DATE <= now < settings.REGISTRATION_CLOSE_DATE
