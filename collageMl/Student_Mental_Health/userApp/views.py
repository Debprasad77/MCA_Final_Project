import joblib
import json
import os
import numpy as np
import pandas as pd
from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponse
from .forms import MentalHealthForm,UserRegistrationForm,CustomPasswordChangeForm
from .models import UserResponse, Prediction
from django.conf import settings

from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from .models import Profile 
from django.contrib.auth.forms import PasswordChangeForm
from .forms import ProfileForm, UserUpdateForm



model_path = os.path.join(settings.BASE_DIR, 'userApp', 'Ml_models', 'multi_model.joblib')
multi_model = joblib.load(model_path)
expected_features = multi_model.feature_names_in_

def preprocess_user_data(user_data):
    # Initial raw dictionary (keys should match lowercase keys)
    raw_data = {
        'Age': user_data['age'],
        'Gender': user_data['gender'],
        'CGPA': user_data['cgpa'],
        'Semester_Credit_Load': user_data['semester_credit_load'],
        'Sleep_Quality': user_data['sleep_quality'],
        'Physical_Activity': user_data['physical_activity'],
        'Diet_Quality': user_data['diet_quality'],
        'Social_Support': user_data['social_support'],
        'Relationship_Status': user_data['relationship_status'],
        'Financial_Stress': user_data['financial_stress'],
        'Substance_Use': user_data.get('substance_use', 'Never'),
        'Counseling_Service_Use': user_data.get('counseling_service_use', 'Never'),
        'Family_History': user_data.get('family_history', 'No'),
        'Chronic_Illness': user_data.get('chronic_illness', 'No'),
        'Extracurricular_Involvement': user_data.get('extracurricular_involvement', 'Moderate'),
        'Residence_Type': user_data.get('residence_type', 'On-Campus'),
        'Course': user_data.get('course', 'Other'),
    }

    # Create a one-row DataFrame
    df = pd.DataFrame([raw_data])

    # One-hot encode
    df_encoded = pd.get_dummies(df)

    # Add missing columns and ensure column order matches training
    for col in expected_features:
        if col not in df_encoded.columns:
            df_encoded[col] = 0  # Fill missing one-hot categories with 0

    # Reorder columns
    df_encoded = df_encoded[expected_features]

    return df_encoded

def generate_user_insights(user_data, model):
    predictions = model.predict(user_data)

    stress_thresholds = [2, 4]
    depression_thresholds = [2, 4]
    anxiety_thresholds = [2, 4]

    stress_level = "Low" if predictions[0][0] < stress_thresholds[0] else \
                  "Moderate" if predictions[0][0] < stress_thresholds[1] else "High"

    depression_level = "Low" if predictions[0][1] < depression_thresholds[0] else \
                      "Moderate" if predictions[0][1] < depression_thresholds[1] else "High"

    anxiety_level = "Low" if predictions[0][2] < anxiety_thresholds[0] else \
                   "Moderate" if predictions[0][2] < anxiety_thresholds[1] else "High"

    def get_stress_recommendations(stress_level, user_data):
        if stress_level == "High":
            return [
                "Practice mindfulness and relaxation techniques.",
                "Consider seeking professional help.",
                "Prioritize sleep and healthy eating."
            ]
        elif stress_level == "Moderate":
            return [
                "Engage in regular physical activity.",
                "Connect with friends and family.",
                "Take breaks and practice time management."
            ]
        else:
            return [
                "Maintain a healthy lifestyle.",
                "Continue with stress-reducing activities."
            ]

    def get_depression_recommendations(depression_level, user_data):
        if depression_level == "High":
            return [
                "Seek professional help immediately.",
                "Prioritize sleep and healthy eating.",
                "Engage in activities you enjoy."
            ]
        elif depression_level == "Moderate":
            return [
                "Consider talking to a therapist.",
                "Practice self-care activities.",
                "Connect with support groups."
            ]
        else:
            return [
                "Maintain a positive outlook.",
                "Continue with activities that promote mental well-being."
            ]

    def get_anxiety_recommendations(anxiety_level, user_data):
        if anxiety_level == "High":
            return [
                "Consult with a mental health professional.",
                "Practice deep breathing exercises.",
                "Limit caffeine and alcohol intake."
            ]
        elif anxiety_level == "Moderate":
            return [
                "Engage in relaxation techniques.",
                "Challenge negative thoughts.",
                "Consider joining a support group."
            ]
        else:
            return [
                "Maintain a healthy lifestyle.",
                "Continue with anxiety-reducing practices."
            ]

    insights = {
        "stress": {
            "level": stress_level,
            "score": float(predictions[0][0]),
            "recommendations": get_stress_recommendations(stress_level, user_data)
        },
        "depression": {
            "level": depression_level,
            "score": float(predictions[0][1]),
            "recommendations": get_depression_recommendations(depression_level, user_data)
        },
        "anxiety": {
            "level": anxiety_level,
            "score": float(predictions[0][2]),
            "recommendations": get_anxiety_recommendations(anxiety_level, user_data)
        }
    }

    return insights


def generate_explanation(prediction):
    try:
        stress, depression, anxiety = prediction[0]
        explanations = []

        if stress >= 4:
            explanations.append("High stress level detected — consider stress management techniques such as mindfulness, exercise, or counseling.")
        elif stress >= 2:
            explanations.append("Moderate stress level — monitor your stress regularly and try healthy coping mechanisms.")
        else:
            explanations.append("Your stress level appears within the normal range.")

        if depression >= 4:
            explanations.append("High depression score — seeking support from a mental health professional is recommended.")
        elif depression >= 2:
            explanations.append("Moderate depression score — be aware of changes in mood and talk to someone you trust.")
        else:
            explanations.append("Your depression score appears within the normal range.")

        if anxiety >= 4:
            explanations.append("High anxiety score — relaxation techniques or speaking to a counselor may help.")
        elif anxiety >= 2:
            explanations.append("Moderate anxiety score — try to manage your triggers and seek support if needed.")
        else:
            explanations.append("Your anxiety score appears within the normal range.")

        return {"explanations": explanations}
    except Exception as e:
        return {
            "explanations": [
                "The model predictions indicate typical mental health patterns for your demographic."
            ],
            "error": str(e)
        }

def home(request):
    if request.method == 'POST':
        form = MentalHealthForm(request.POST)
        if form.is_valid():
            try:
                user_data = form.cleaned_data
                model_path = os.path.join(settings.BASE_DIR, 'userApp', 'Ml_models', 'multi_model.joblib')
                multi_model = joblib.load(model_path)
                processed_data = preprocess_user_data(user_data)
                prediction = multi_model.predict(processed_data)
                insights = generate_user_insights(processed_data, multi_model)
                explanation = generate_explanation(prediction)

                user_response = UserResponse(
                    user_id=request.user.id if request.user.is_authenticated else None,
                    age=user_data['age'],
                    gender=user_data['gender'],
                    cgpa=user_data['cgpa'],
                    semester_credit_load=user_data['semester_credit_load'],
                    sleep_quality=user_data['sleep_quality'],
                    physical_activity=user_data['physical_activity'],
                    diet_quality=user_data['diet_quality'],
                    social_support=user_data['social_support'],
                    relationship_status=user_data['relationship_status'],
                    financial_stress=user_data['financial_stress'],
                    substance_use=user_data.get('substance_use', 'Never'),
                    counseling_service_use=user_data.get('counseling_service_use', 'Never'),
                    family_history=user_data.get('family_history', 'No'),
                    chronic_illness=user_data.get('chronic_illness', 'No'),
                    extracurricular_involvement=user_data.get('extracurricular_involvement', 'Moderate'),
                    residence_type=user_data.get('residence_type', 'On-Campus')
                )
                print("Saving UserResponse...")
                user_response.save()
                print("UserResponse saved with ID:", user_response.id)

                prediction_obj = Prediction(
                    user_response=user_response,
                    stress_level=prediction[0][0],
                    depression_score=prediction[0][1],
                    anxiety_score=prediction[0][2],
                )
                print("Saving Prediction...")
                prediction_obj.save()
                print("Prediction saved.")

                return render(request, 'result.html', {
                    'prediction': prediction.tolist(),
                    'insights': insights,
                    'explanation': explanation
                })

            except Exception as e:
                try:
                    return render(request, 'error.html', {
                        'error_message': f"An error occurred during prediction: {str(e)}"
                    })
                except:
                    return HttpResponse(f"""
                        <h1>Error Occurred</h1>
                        <p>{str(e)}</p>
                        <a href="/">Return to Assessment</a>
                    """)

    form = MentalHealthForm()
    return render(request, 'index.html', {'form': form})


def predict_api(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body) if request.body else request.POST
            user_data = {
                'age': float(data.get('age')),
                'gender': data.get('gender'),
                'cgpa': float(data.get('cgpa')),
                'semester_credit_load': float(data.get('semester_credit_load')),
                'sleep_quality': data.get('sleep_quality'),
                'physical_activity': data.get('physical_activity'),
                'diet_quality': data.get('diet_quality'),
                'social_support': data.get('social_support'),
                'relationship_status': data.get('relationship_status'),
                'financial_stress': float(data.get('financial_stress')),
                'substance_use': data.get('substance_use', 'Never'),
                'counseling_service_use': data.get('counseling_service_use', 'Never'),
                'extracurricular_involvement': data.get('extracurricular_involvement', 'Moderate'),
                'residence_type': data.get('residence_type', 'On-Campus'),
                'family_history': data.get('family_history', 'No'),
                'chronic_illness': data.get('chronic_illness', 'No'),
                'course': data.get('course', 'Other'),
            }

            model_path = os.path.join(settings.BASE_DIR, 'userApp', 'Ml_models', 'multi_model.joblib')
            multi_model = joblib.load(model_path)
            processed_data = preprocess_user_data(user_data)
            prediction = multi_model.predict(processed_data)

            insights = generate_user_insights(processed_data, multi_model)
            explanation = generate_explanation(prediction)
            print(insights)

            return JsonResponse({
                'status': 'success',
                'prediction': prediction.tolist(),
                'insights': insights,
                'explanation': explanation
            })
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    return JsonResponse({'error': 'Invalid request method'}, status=400)




def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('home')
        return render(request, 'login.html', {'form': form})
    
    # GET request
    form = AuthenticationForm()
    return render(request, 'login.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('home')

@login_required
def profile_view(request):
    try:
        profile = request.user.profile
    except Profile.DoesNotExist:  # Now properly referenced
        # Create profile if missing
        Profile.objects.create(user=request.user)
        profile = request.user.profile

    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile has been updated!')
            return redirect('profile')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ProfileForm(instance=profile)

    return render(request, 'profile.html', {'form': form})

@login_required
def settings_view(request):
    user_form = UserUpdateForm(instance=request.user)
    password_form = PasswordChangeForm(request.user)
    profile_form = ProfileForm(instance=request.user.profile)

    if request.method == 'POST':
        if 'update_account' in request.POST:
            user_form = UserUpdateForm(request.POST, instance=request.user)
            if user_form.is_valid():
                user_form.save()
                messages.success(request, 'Your account details have been updated!')
                return redirect('settings')
        
        elif 'change_password' in request.POST:
            password_form = PasswordChangeForm(request.user, request.POST)
            if password_form.is_valid():
                password_form.save()
                messages.success(request, 'Your password has been changed!')
                return redirect('settings')

        elif 'update_profile' in request.POST:
            profile_form = ProfileForm(request.POST, request.FILES, instance=request.user.profile)
            if profile_form.is_valid():
                profile_form.save()
                messages.success(request, 'Your profile has been updated!')
                return redirect('settings')

    context = {
        'user_form': user_form,
        'password_form': password_form,
        'profile_form': profile_form
    }
    return render(request, 'settings.html', context)



def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            form.save()  # Saves user including first/last name and email
            username = form.cleaned_data.get('username')
            messages.success(request, f'Account created for {username}. You can now log in.')
            return redirect('login')
    else:
        form = UserRegistrationForm()
    return render(request, 'register.html', {'form': form})



def change_password(request):
    if request.method == 'POST':
        form = CustomPasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Keeps the user logged in
            messages.success(request, 'Your password was successfully updated!')
            return redirect('profile')  # or wherever you want to redirect
        else:
            messages.error(request, 'Please correct the error below.')
    else:
        form = CustomPasswordChangeForm(user=request.user)
    return render(request, 'change_password.html', {'form': form})