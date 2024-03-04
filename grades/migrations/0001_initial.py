# Generated by Django 4.2.6 on 2023-10-26 18:16

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Assignment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200)),
                ('description', models.TextField(blank=True, null=True)),
                ('deadline', models.DateTimeField()),
                ('weight', models.IntegerField()),
                ('points', models.IntegerField()),
            ],
        ),
        migrations.CreateModel(
            name='Submission',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('file', models.FileField(upload_to='')),
                ('score', models.DecimalField(decimal_places=2, max_digits=6)),
                ('assignment', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='grades.assignment')),
                ('author', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('grader', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='graded_set', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]