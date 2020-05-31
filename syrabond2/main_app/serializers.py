from rest_framework import serializers

from .models import Switch, Sensor


class SwitchSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Switch
        fields = ['title', 'uid']