from unittest.mock import Mock, patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.utils import timezone

from apps.core.models import Gincana, Setor, Tarefa, send_whatsapp_message

class TarefaSchedulingTests(TestCase):
    def setUp(self):
        self.gincana = Gincana.objects.create(
            nome='Gincana',
            data_inicio='2026-01-01',
            data_fim='2026-12-31',
            descricao='Descricao',
            grupo_whatsapp='group@g.us',
        )
        self.setor = Setor.objects.create(nome='Setor', emoji='S')

    @patch('apps.core.models.send_whatsapp_message.apply_async')
    def test_repeated_save_schedules_once(self, apply_async):
        apply_async.return_value.id = 'task-id'
        tarefa = Tarefa.objects.create(
            titulo='Tarefa',
            gincana=self.gincana,
            setor=self.setor,
            disponivel_em=timezone.now() + timezone.timedelta(hours=1),
            arquivo=SimpleUploadedFile('tarefa.pdf', b'%PDF'),
        )

        tarefa.save()

        apply_async.assert_called_once_with(args=[tarefa.id], eta=tarefa.disponivel_em)

    @patch('apps.core.models.requests.post')
    def test_successful_send_is_not_sent_again(self, post):
        post.return_value = Mock(status_code=200, content=b'ok', raise_for_status=Mock())
        tarefa = Tarefa.objects.create(
            titulo='Tarefa',
            gincana=self.gincana,
            setor=self.setor,
            disponivel_em=timezone.now() - timezone.timedelta(minutes=1),
            arquivo=SimpleUploadedFile('tarefa.pdf', b'%PDF'),
        )

        send_whatsapp_message(tarefa.id)
        send_whatsapp_message(tarefa.id)

        post.assert_called_once()
        self.assertIsNotNone(Tarefa.objects.get(pk=tarefa.pk).sent_at)

        self.assertEqual(post.call_args.kwargs['headers'], {'token': 'test'})
        self.assertEqual(post.call_args.kwargs['timeout'], (10, 120))
