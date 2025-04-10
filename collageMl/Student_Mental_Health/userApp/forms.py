from django import forms

class MentalHealthForm(forms.Form):
    age = forms.IntegerField(label='Age')
    gender = forms.CharField(max_length=10, label='Gender')
    course = forms.CharField(max_length=50, label='Course')
    cgpa = forms.DecimalField(max_digits=3, decimal_places=2, label='CGPA')
    semester_credit_load = forms.IntegerField(label='Semester Credit Load')
    sleep_quality = forms.CharField(max_length=10, label='Sleep Quality')
    physical_activity = forms.CharField(max_length=10, label='Physical Activity')
    diet_quality = forms.CharField(max_length=10, label='Diet Quality')
    social_support = forms.CharField(max_length=10, label='Social Support')
    relationship_status = forms.CharField(max_length=10, label='Relationship Status')
    financial_stress = forms.IntegerField(label='Financial Stress')

    # Add more fields as necessary
