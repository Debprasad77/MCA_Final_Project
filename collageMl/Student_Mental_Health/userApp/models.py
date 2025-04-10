from django.db import models
from django.contrib.auth.models import User

class UserResponse(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    age = models.IntegerField()
    gender = models.CharField(max_length=10)
    cgpa = models.DecimalField(max_digits=3, decimal_places=2)
    semester_credit_load = models.IntegerField()
    sleep_quality = models.CharField(max_length=10)
    physical_activity = models.CharField(max_length=10)
    diet_quality = models.CharField(max_length=10)
    social_support = models.CharField(max_length=10)
    relationship_status = models.CharField(max_length=10)
    financial_stress = models.IntegerField()
    substance_use = models.CharField(max_length=10, blank=True, null=True)
    counseling_service_use = models.CharField(max_length=10, blank=True, null=True)
    family_history = models.CharField(max_length=10, blank=True, null=True)
    chronic_illness = models.CharField(max_length=10, blank=True, null=True)
    extracurricular_involvement = models.CharField(max_length=10, blank=True, null=True)
    residence_type = models.CharField(max_length=10, blank=True, null=True)

    def __str__(self):
        return f"Response #{self.id}"

class Prediction(models.Model):
    user_response = models.ForeignKey(UserResponse, on_delete=models.CASCADE)
    stress_level = models.DecimalField(max_digits=3, decimal_places=2)
    depression_score = models.DecimalField(max_digits=3, decimal_places=2)
    anxiety_score = models.DecimalField(max_digits=3, decimal_places=2)

    def __str__(self):
        return f"Prediction for {self.user_response}"