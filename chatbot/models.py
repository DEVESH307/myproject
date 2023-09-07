from django.db import models

# Create your models here.
class Transaction(models.Model):
    client_id = models.CharField(max_length=10)
    trn_number = models.CharField(max_length=10)
    Amount = models.DecimalField(max_digits=10, decimal_places=2)
    trn_date = models.DateField()
    Description = models.CharField(max_length=100)

    def __str__(self):
        return f"Transaction {self.trn_number} - {self.Description}"
