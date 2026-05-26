from django.db import models
from django.contrib.auth.models import User

class Transaction(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='transactions')
    description = models.CharField(max_length=200)
    montant = models.DecimalField(max_digits=10, decimal_places=2)
    TYPE_CHOICES = [('revenu', 'Revenu'), ('depense', 'Dépense')]
    type = models.CharField(max_length=7, choices=TYPE_CHOICES)
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.description} - {self.montant}€ ({self.type})"

# Create your models here.

class LoginAttempt(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    was_successful = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-timestamp']