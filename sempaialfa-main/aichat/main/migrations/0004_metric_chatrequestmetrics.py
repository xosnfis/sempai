# Generated manually

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0003_remove_account_user_remove_calendarevent_user_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='Metric',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(db_index=True, max_length=100)),
                ('category', models.CharField(choices=[('response_quality', 'Качество ответов'), ('action_performance', 'Выполнение действий'), ('performance', 'Производительность'), ('reliability', 'Надежность'), ('security', 'Безопасность'), ('user_experience', 'Пользовательский опыт'), ('file_processing', 'Обработка файлов'), ('data_accuracy', 'Точность данных'), ('calendar', 'Работа с календарем'), ('formatting', 'Форматирование')], db_index=True, max_length=50)),
                ('value', models.FloatField()),
                ('target_value', models.FloatField(blank=True, null=True)),
                ('unit', models.CharField(default='percent', max_length=20)),
                ('period_start', models.DateTimeField(db_index=True)),
                ('period_end', models.DateTimeField(db_index=True)),
                ('calculated_at', models.DateTimeField(auto_now_add=True)),
                ('sample_size', models.IntegerField(default=0)),
                ('metadata', models.JSONField(blank=True, default=dict)),
            ],
            options={
                'verbose_name': 'Метрика',
                'verbose_name_plural': 'Метрики',
                'ordering': ['-calculated_at', '-period_end'],
            },
        ),
        migrations.CreateModel(
            name='ChatRequestMetrics',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('processing_time', models.FloatField(blank=True, null=True)),
                ('llm_processing_time', models.FloatField(blank=True, null=True)),
                ('has_action', models.BooleanField(default=False)),
                ('action_success', models.BooleanField(blank=True, null=True)),
                ('has_files', models.BooleanField(default=False)),
                ('files_processed', models.IntegerField(default=0)),
                ('files_failed', models.IntegerField(default=0)),
                ('message_blocked', models.BooleanField(default=False)),
                ('response_blocked', models.BooleanField(default=False)),
                ('context_used', models.BooleanField(default=False)),
                ('response_length', models.IntegerField(default=0)),
                ('metadata', models.JSONField(blank=True, default=dict)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('chat_request', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='metrics', to='main.chatrequest')),
            ],
            options={
                'verbose_name': 'Метрики запроса',
                'verbose_name_plural': 'Метрики запросов',
            },
        ),
        migrations.AddIndex(
            model_name='metric',
            index=models.Index(fields=['name', '-calculated_at'], name='main_metric_name_ca_idx'),
        ),
        migrations.AddIndex(
            model_name='metric',
            index=models.Index(fields=['category', '-calculated_at'], name='main_metric_catego_idx'),
        ),
        migrations.AddIndex(
            model_name='metric',
            index=models.Index(fields=['period_start', 'period_end'], name='main_metric_period_idx'),
        ),
        migrations.AddIndex(
            model_name='chatrequestmetrics',
            index=models.Index(fields=['chat_request'], name='main_chatreq_chat_re_idx'),
        ),
    ]

