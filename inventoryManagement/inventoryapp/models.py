from django.db import models
from django.utils import timezone


# Create your models here.
class Quality(models.Model):
    qualities = models.CharField(max_length=50)

    

class Record(models.Model):
    sr_no= models.IntegerField()
    party_name= models.CharField(max_length=50,default="no")
    bill_no = models.IntegerField()
    bill_date = models.CharField(max_length=30)
    bill_amount = models.FloatField(max_length=15)
    lot_no = models.IntegerField() 
    quality = models.CharField(max_length=100)
    than = models.IntegerField()
    mtrs = models.FloatField(max_length=15)
    bale = models.IntegerField()
    rate = models.FloatField(max_length=15)
    lr_no = models.IntegerField()
    order_no = models.IntegerField()
    state_choices=(('state1','In transit'), ('state2','Order recieved'), ('state3','In godown'), ('state4','done'))
    state = models.CharField(max_length=10,default='Transit')
    bale_recieved = models.IntegerField(default=0)
    recieving_date = models.DateField(default=timezone.now().strftime("%Y-%m-%d"))
    quality2 = models.CharField(max_length=20,default="-")
    total_bale = models.IntegerField()
    
    # def __str__(self):
    #     return self.sr_no +" " +self.party_name



class ProcessingPartyName(models.Model):
    processing_party = models.CharField(max_length=50)