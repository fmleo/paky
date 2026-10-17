from django.db import migrations, models
import django.core.validators


class Migration(migrations.Migration):
    dependencies = [
        ('core', '0002_alter_setor_options'),
    ]

    operations = [
        migrations.AlterField(
            model_name='tarefa',
            name='arquivo',
            field=models.FileField(
                upload_to='.',
                validators=[django.core.validators.FileExtensionValidator(allowed_extensions=['pdf'])],
            ),
        ),
        migrations.AddField(
            model_name='tarefa',
            name='celery_task_id',
            field=models.CharField(editable=False, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='tarefa',
            name='sent_at',
            field=models.DateTimeField(editable=False, null=True),
        ),
    ]
