# Generated by Django 3.2.15 on 2024-09-02 00:52

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('registration', '0007_auto_20240826_2200'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='application',
            name='what_past_experience',
        ),
        migrations.RemoveField(
            model_name='application',
            name='what_technical_experience',
        ),
        migrations.RemoveField(
            model_name='application',
            name='why_participate',
        ),
    ]
