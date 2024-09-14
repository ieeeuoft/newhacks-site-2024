# Generated by Django 3.2.15 on 2024-09-14 03:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('registration', '0008_revert_0007_changes'),
    ]

    operations = [
        migrations.AddField(
            model_name='application',
            name='free_response_gender',
            field=models.CharField(blank=True, default='', help_text="If you selected 'Prefer to Self-Describe', please specify.", max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='application',
            name='free_response_pronouns',
            field=models.CharField(blank=True, default='', help_text="If selected 'Other', please specify", max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='application',
            name='gender',
            field=models.CharField(choices=[(None, ''), ('man', 'Man'), ('woman', 'Woman'), ('non-binary', 'Non-Binary'), ('prefer-to-self-describe', 'Prefer to Self-Describe'), ('prefer-to-not-answer', 'Prefer to not Answer')], default='', max_length=50),
        ),
        migrations.AlterField(
            model_name='application',
            name='pronouns',
            field=models.CharField(choices=[(None, ''), ('he-him', 'he/him'), ('he-they', 'he/they'), ('she-her', 'she/her'), ('she-they', 'she/they'), ('they-them', 'they/them'), ('other', 'other'), ('no-answer', 'prefer not to answer')], default='', max_length=50),
        ),
    ]
