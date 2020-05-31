from rest_framework import viewsets
from rest_framework import permissions

from .models import Switch
from .serializers import SwitchSerializer


class SwitchViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = Switch.objects.all()
    serializer_class = SwitchSerializer
    permission_classes = [permissions.IsAuthenticated]