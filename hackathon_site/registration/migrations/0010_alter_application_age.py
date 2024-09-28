# Generated by Django 3.2.15 on 2024-09-28 22:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("registration", "0009_auto_20240925_2109")]

    operations = [
        migrations.AlterField(
            model_name="application",
            name="age",
            field=models.PositiveIntegerField(
                choices=[
                    (None, ""),
                    (17, "17"),
                    (18, "18"),
                    (19, "19"),
                    (20, "20"),
                    (21, "21"),
                    (22, "22"),
                    (23, "22+"),
                ]
            ),
        )
    ]
