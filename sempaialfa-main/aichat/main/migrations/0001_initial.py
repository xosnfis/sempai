# Generated manually

from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='ChatRequest',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('status', models.CharField(choices=[('pending', 'Ожидает обработки'), ('processing', 'Обрабатывается'), ('completed', 'Завершено'), ('failed', 'Ошибка')], default='pending', max_length=20)),
                ('message', models.TextField(blank=True)),
                ('chat_history', models.JSONField(blank=True, default=list)),
                ('user_data', models.JSONField(blank=True, default=dict)),
                ('files_data', models.JSONField(blank=True, default=list)),
                ('response', models.TextField(blank=True, null=True)),
                ('action', models.JSONField(blank=True, default=dict, null=True)),
                ('error', models.TextField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('completed_at', models.DateTimeField(blank=True, null=True)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='chatrequest',
            index=models.Index(fields=['status', 'created_at'], name='main_chatre_status_created_idx'),
        ),
    ]

