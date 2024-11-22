import base64
import uuid

import requests
from django.conf import settings
from django.core.validators import FileExtensionValidator
from django.db import models
from django.utils import timezone
from django.utils.text import slugify

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

    def arquivo_base64(self):
        with self.arquivo.open('rb') as f:
            return base64.b64encode(f.read()).decode('utf-8')

    def pretty_caption(self) -> str:
        return f"""{self.titulo}
{self.setor}
{self.disponivel_em:%d/%m/%Y %R}"""

    def __str__(self):
        return self.titulo

    def save(self, *args, **kwargs):
        self.arquivo.name = f'{slugify(self.gincana.nome)}/{self.id}.pdf'

        super(Tarefa, self).save(*args, **kwargs)

        if self.disponivel_em > timezone.now():
            task = send_whatsapp_message.apply_async(args=[self.id], eta=self.disponivel_em)


@app.task
def send_whatsapp_message(tarefa_id: uuid.uuid4):
    tarefa = Tarefa.objects.get(id=tarefa_id)

    data = {
        "Phone": tarefa.gincana.grupo_whatsapp,
        "Filename": f"{slugify(tarefa.titulo)}.pdf",
        "Document": f"data:application/octet-stream;base64,{tarefa.arquivo_base64()}",
        "Caption": tarefa.pretty_caption()
    }

    headers = {"token": settings.WUZAPI_TOKEN}

    resp = requests.post(settings.WUZAPI_URL + "/chat/send/document", json=data, headers=headers)

    print(resp.content)
