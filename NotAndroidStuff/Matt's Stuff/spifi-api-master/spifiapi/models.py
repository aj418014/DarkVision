from django.db import models

# Create your models here.

class Sensor(models.Model):
    lat = models.FloatField()
    lng = models.FloatField()

    def __str__(self):
        return str(self.id)

class Target(models.Model):
    time = models.DateTimeField(auto_now= True)
    sensor = models.ForeignKey(Sensor, on_delete=models.CASCADE)
    addr = models.CharField(max_length = 20)
	
    def getTargetLat(self):
        return self.sensor.lat
        
    def getTargetLng(self):
        return self.sensor.lng

    def __str__(self):
        return self.addr