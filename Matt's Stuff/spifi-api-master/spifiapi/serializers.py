from spifiapi.models import Sensor, Target
from rest_framework import serializers


class SensorSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Sensor
        fields = ('lat', 'lng')


class TargetSerializer(serializers.HyperlinkedModelSerializer):
    targetLng = serializers.ReadOnlyField(source='getTargetLng', read_only = True)
    targetLat = serializers.ReadOnlyField(source='getTargetLat', read_only = True)
    class Meta:
        model = Target
        fields = ('sensor', 'time', 'addr', 'targetLat', 'targetLng')
