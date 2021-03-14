from django.db import models
from django.utils import timezone


class CityMaster(models.Model):
    city = models.CharField(null=True,max_length=50)
