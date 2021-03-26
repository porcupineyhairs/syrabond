from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.staticfiles.storage import staticfiles_storage
from django.views.generic import ListView

from rest_framework import viewsets
from rest_framework import permissions

from .models import Switch, Sensor, Premise
from .serializers import SwitchSerializer


class Facility:

    MODELS = [
        'Switch',
        'Sensor'
    ]

    def __init__(self):
        self.resources = {}
        self.premises = {}
        self.load_resources()

    def load_resources(self):
        for mod in self.MODELS:
            model = globals()[mod]
            qs = model.objects.all()
            for obj in qs:
                self.resources.update({obj.uid: obj})



class SwitchesListView(ListView):
    template_name = 'index.html'
    model = Switch


class PremisesListView(ListView):
    template_name = 'premises.html'
    model = Premise


def switch(request, uid=None):
    facility.resources.get(uid).toggle()
    return HttpResponseRedirect('/switches/')



class SwitchViewSet(viewsets.ModelViewSet):
    """
    Switches API endpoint
    """
    lookup_value_regex = '[^/]+'
    queryset = Switch.objects.all()
    serializer_class = SwitchSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_update(self, serializer: SwitchSerializer):

        if serializer.initial_data.get('state_') != serializer.instance.state.current:
            serializer.instance.toggle()
        serializer.save()


#facility = Facility()
