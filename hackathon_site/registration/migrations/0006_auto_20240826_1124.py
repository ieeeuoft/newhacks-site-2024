# Generated by Django 3.2.15 on 2024-08-26 15:24

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("registration", "0005_auto_20240630_1437"),
    ]

    operations = [
        migrations.RemoveField(model_name="application", name="what_past_experience",),
        migrations.RemoveField(
            model_name="application", name="what_technical_experience",
        ),
        migrations.RemoveField(model_name="application", name="why_participate",),
    ]
