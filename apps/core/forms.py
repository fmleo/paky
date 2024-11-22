import requests
from django import forms
from django.conf import settings

from apps.core.models import Tarefa


class TarefaForm(forms.ModelForm):
    class Meta:
        model = Tarefa
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        response = requests.get(settings.WUZAPI_URL + "/group/list",
                                headers={"token": settings.WUZAPI_TOKEN})

        if response.status_code == 200:
            groups = []
            for group in response.json()["data"]["Groups"]:
                groups.append((group["JID"], group["Name"]))

            if groups:
                self.fields["grupo_whatsapp"] = forms.ChoiceField(choices=groups)
