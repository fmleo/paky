import base64
import uuid

import requests
from django.conf import settings
from django.core.validators import FileExtensionValidator
from django.db import models
from django.utils import timezone
from django.utils.text import slugify
from django.utils.timezone import localtime

from paky.celery import app


class Gincana(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nome = models.CharField(max_length=150)
    data_inicio = models.DateField()
    data_fim = models.DateField()
    descricao = models.TextField(verbose_name='Descrição')
    grupo_whatsapp = models.CharField(max_length=150, help_text="Formato: 120363345631476657@g.us")

    def __str__(self):
        return self.nome


class Setor(models.Model):
    nome = models.CharField(max_length=150)
    emoji = models.CharField(max_length=2)

    def __str__(self):
        return f"{self.emoji} {self.nome}"

    class Meta:
        verbose_name_plural = 'Setores'


class Tarefa(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    titulo = models.CharField(max_length=150)
    gincana = models.ForeignKey('Gincana', on_delete=models.CASCADE)
    arquivo = models.FileField(upload_to=".", validators=[FileExtensionValidator(allowed_extensions=['pdf'])])
    setor = models.ForeignKey('Setor', on_delete=models.SET_NULL, null=True)
    disponivel_em = models.DateTimeField()
    responsavel = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True)
    celery_task_id = models.CharField(max_length=255, null=True, editable=False)
    sent_at = models.DateTimeField(null=True, editable=False)

    def arquivo_base64(self):
        with self.arquivo.open('rb') as f:
            return base64.b64encode(f.read()).decode('utf-8')

    def pretty_caption(self) -> str:
        local_time = localtime(self.disponivel_em)
        return f"""{self.titulo}
{self.setor}
{local_time:%d/%m/%Y %R}"""

    def __str__(self):
        return self.titulo

    def save(self, *args, **kwargs):
        is_new = self._state.adding
        previous_disponivel_em = None
        if not is_new:
            previous_disponivel_em = type(self).objects.values_list(
                'disponivel_em', flat=True
            ).get(pk=self.pk)

        self.arquivo.name = f'{slugify(self.gincana.nome)}/{self.id}.pdf'

        super().save(*args, **kwargs)

        disponivel_em_changed = previous_disponivel_em != self.disponivel_em
        if (
            (is_new or disponivel_em_changed)
            and self.disponivel_em > timezone.now()
            and self.sent_at is None
        ):
            task = send_whatsapp_message.apply_async(args=[self.id], eta=self.disponivel_em)
            type(self).objects.filter(pk=self.pk, celery_task_id__isnull=True).update(
                celery_task_id=task.id
            )
            self.celery_task_id = task.id


@app.task
def send_whatsapp_message(tarefa_id: uuid.UUID):
    from django.db import transaction

    with transaction.atomic():
        tarefa = Tarefa.objects.select_for_update().get(id=tarefa_id)
        if tarefa.sent_at is not None:
            return
        data = {
            "Phone": tarefa.gincana.grupo_whatsapp,
            "Filename": f"{slugify(tarefa.titulo)}.pdf",
            "Document": f"data:application/octet-stream;base64,{tarefa.arquivo_base64()}",
            "Caption": tarefa.pretty_caption()
        }

    headers = {"token": settings.WUZAPI_TOKEN}

    resp = requests.post(
        settings.WUZAPI_URL + "/chat/send/document",
        json=data,
        headers=headers,
        timeout=(10, 120),
    )
    resp.raise_for_status()

    with transaction.atomic():
        tarefa = Tarefa.objects.select_for_update().get(id=tarefa_id)
        if tarefa.sent_at is None:
            tarefa.sent_at = timezone.now()
            tarefa.save(update_fields=["sent_at"])
            print(resp.content)
