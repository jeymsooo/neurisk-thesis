from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import UserProfile, EMGData, FeatureSet, RiskScore, TrainingAssignment, Session
from .serializers import UserProfileSerializer, EMGDataSerializer, FeatureSetSerializer, RiskScoreSerializer, TrainingAssignmentSerializer, SessionSerializer
import numpy as np
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from feature_extraction.emg_features import extract_features
import pandas as pd
import joblib
from prediction.predictor import InjuryRiskPredictor
from rest_framework.generics import ListAPIView
from django.db.models import Max
from django.utils import timezone

# Create your views here.

class UserAndEMGDataUploadView(APIView):
    """
    Custom endpoint to receive user demographics and raw EMG data in a single POST request.
    """
    def post(self, request, format=None):
        user_data = request.data.get('user')
        emg_data = request.data.get('emg_data')
        if not user_data or not emg_data:
            return Response({'error': 'user and emg_data fields are required.'}, status=status.HTTP_400_BAD_REQUEST)

        # Create or get user profile
        user_serializer = UserProfileSerializer(data=user_data)
        if user_serializer.is_valid():
            user = user_serializer.save()
        else:
            return Response(user_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # Create EMG data entry
        emg_data_obj = {
            'user': user.id,
            'raw_data': emg_data
        }
        emg_serializer = EMGDataSerializer(data=emg_data_obj)
        if emg_serializer.is_valid():
            emg_instance = emg_serializer.save()
        else:
            # Rollback user if EMG data fails
            user.delete()
            return Response(emg_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            'user': user_serializer.data,
            'emg_data': emg_serializer.data
        }, status=status.HTTP_201_CREATED)

class FeatureExtractionView(APIView):
    """
    Custom endpoint to extract features from EMGData.
    POST: {"emg_data_id": <id>, "fs": <sampling_frequency>}
    """
    def post(self, request, format=None):
        emg_data_id = request.data.get('emg_data_id')
        fs = request.data.get('fs', 1000)  # Default to 1000 Hz if not provided
        if not emg_data_id:
            return Response({'error': 'emg_data_id is required.'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            emg_data = EMGData.objects.get(id=emg_data_id)
        except EMGData.DoesNotExist:
            return Response({'error': 'EMGData not found.'}, status=status.HTTP_404_NOT_FOUND)
        raw_signal = np.array(emg_data.raw_data)
        features = extract_features(raw_signal, fs)
        feature_set = FeatureSet.objects.create(emg_data=emg_data, features=features)
        serializer = FeatureSetSerializer(feature_set)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

# Training assignment logic (from streamlit_app.py)
def get_training_assignment(risk_level):
    if risk_level == "low":
        return (
            "Low Risk Training Regime:\n"
            "- Continue regular strength and conditioning.\n"
            "- Emphasize warm-up, cool-down, and recovery.\n"
            "- Monitor training load.\n"
            "- Dynamic warm-up, plyometrics, activation exercises before practice.\n"
            "- Full participation in team drills.\n"
            "- Static stretching, foam rolling, hydration after practice."
        )
    elif risk_level == "medium":
        return (
            "Medium Risk Training Regime:\n"
            "- Add targeted neuromuscular and eccentric strengthening.\n"
            "- Monitor fatigue and muscle imbalances.\n"
            "- Integrate recovery modalities.\n"
            "- Dynamic warm-up with balance/proprioceptive drills.\n"
            "- Eccentric strengthening, neuromuscular exercises during practice.\n"
            "- Static stretching, yoga, foam rolling, ice/compression after practice."
        )
    elif risk_level == "high":
        return (
            "High Risk Training Regime:\n"
            "- Supervised rehabilitation with a physiotherapist.\n"
            "- Individualized corrective exercise program.\n"
            "- Gradual return-to-play protocol.\n"
            "- Supervised rehab warm-up, corrective exercises before practice.\n"
            "- Modified/limited participation in team drills.\n"
            "- Extended cool-down, physiotherapist-guided recovery, education after practice."
        )
    else:
        return "No recommendation available."

class PredictionAndTrainingView(APIView):
    """
    Custom endpoint to predict injury risk and assign training.
    POST: {"feature_set_id": <id>, "user": {...}, "muscle_group": "quadriceps"}
    """
    def post(self, request, format=None):
        feature_set_id = request.data.get('feature_set_id')
        user_data = request.data.get('user')
        muscle_group = request.data.get('muscle_group')
        if not feature_set_id or not user_data or not muscle_group:
            return Response({'error': 'feature_set_id, user, and muscle_group are required.'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            feature_set = FeatureSet.objects.get(id=feature_set_id)
        except FeatureSet.DoesNotExist:
            return Response({'error': 'FeatureSet not found.'}, status=status.HTTP_404_NOT_FOUND)
        emg_features = feature_set.features
        # Prepare user inputs (add BMI if possible)
        user_inputs = user_data.copy()
        if 'height' in user_inputs and 'weight' in user_inputs:
            user_inputs['bmi'] = user_inputs['weight'] / ((user_inputs['height'] / 100) ** 2)
        else:
            user_inputs['bmi'] = 0
        # Predict risk
        predictor = InjuryRiskPredictor()
        # Dummy raw_emg_signal (not used in this context, features already extracted)
        # We'll use the predictor's prepare_features_for_prediction
        X_pred = predictor.prepare_features_for_prediction(user_inputs, emg_features, muscle_group)
        model = predictor.models[muscle_group]
        expected_features = list(getattr(model, "feature_names_in_", []))
        if expected_features:
            for col in expected_features:
                if col not in X_pred.columns:
                    X_pred[col] = 0
            X_pred = X_pred[expected_features]
        risk_level = model.predict(X_pred)[0]
        # Store risk score
        risk_score = RiskScore.objects.create(
            feature_set=feature_set,
            score=0,  # If you have a numeric score, set it here
            level=risk_level
        )
        # Assign training
        assignment_text = get_training_assignment(risk_level)
        training_assignment = TrainingAssignment.objects.create(
            risk_score=risk_score,
            assignment=assignment_text
        )
        return Response({
            'risk_score': risk_level,
            'training_assignment': assignment_text
        }, status=status.HTTP_200_OK)

class UserRiskScoreListView(APIView):
    """
    GET: /api/user_risk_scores/?name=<name>
    Returns a list of users (optionally filtered by name) with their latest risk score and training assignment.
    """
    def get(self, request, format=None):
        name_query = request.GET.get('name', None)
        users = UserProfile.objects.all()
        if name_query:
            users = users.filter(name__icontains=name_query)
        results = []
        for user in users:
            emg_data = user.emg_data.order_by('-timestamp').first()
            if not emg_data:
                continue
            feature_set = emg_data.feature_sets.order_by('-timestamp').first()
            if not feature_set:
                continue
            risk_score = feature_set.risk_scores.order_by('-timestamp').first()
            if not risk_score:
                continue
            training_assignment = risk_score.training_assignments.order_by('-timestamp').first()
            results.append({
                'user': {
                    'id': user.id,
                    'name': user.name,
                    'age': user.age,
                    'height': user.height,
                    'weight': user.weight,
                    'training_frequency': user.training_frequency,
                    'previous_injury': user.previous_injury,
                    'muscle_group': user.muscle_group,
                    'contraction_type': user.contraction_type,
                },
                'risk_score': risk_score.level,
                'training_assignment': training_assignment.assignment if training_assignment else None,
                'timestamp': str(risk_score.timestamp)
            })
        return Response(results, status=status.HTTP_200_OK)

class RealTimeSessionView(APIView):
    """
    POST: /api/submit_session/
    Receives user demographics and raw EMG data, extracts features, predicts risk, stores all results, and returns risk score and training assignment.
    """
    def post(self, request, format=None):
        user_data = request.data.get('user')
        emg_data = request.data.get('emg_data')
        fs = request.data.get('fs', 1000)
        muscle_group = user_data.get('muscle_group') if user_data else None
        if not user_data or not emg_data or not muscle_group:
            return Response({'error': 'user, emg_data, and muscle_group are required.'}, status=status.HTTP_400_BAD_REQUEST)
        # Create user profile
        user_serializer = UserProfileSerializer(data=user_data)
        if user_serializer.is_valid():
            user = user_serializer.save()
        else:
            return Response(user_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        # Store EMG data
        emg_data_obj = EMGData.objects.create(user=user, raw_data=emg_data)
        # Extract features
        raw_signal = np.array(emg_data)
        features = extract_features(raw_signal, fs)
        features = convert_numpy_types(features)
        feature_set = FeatureSet.objects.create(emg_data=emg_data_obj, features=features)
        # Prepare user inputs (add BMI if possible)
        user_inputs = user_data.copy()
        if 'height' in user_inputs and 'weight' in user_inputs:
            user_inputs['bmi'] = user_inputs['weight'] / ((user_inputs['height'] / 100) ** 2)
        else:
            user_inputs['bmi'] = 0
        # Predict risk
        predictor = InjuryRiskPredictor()
        X_pred = predictor.prepare_features_for_prediction(user_inputs, features, muscle_group)
        model = predictor.models[muscle_group]
        expected_features = list(getattr(model, "feature_names_in_", []))
        if expected_features:
            for col in expected_features:
                if col not in X_pred.columns:
                    X_pred[col] = 0
            X_pred = X_pred[expected_features]
        risk_level = model.predict(X_pred)[0]
        # Store risk score
        risk_score = RiskScore.objects.create(
            feature_set=feature_set,
            score=0,  # If you have a numeric score, set it here
            level=risk_level
        )
        # Assign training
        assignment_text = get_training_assignment(risk_level)
        training_assignment = TrainingAssignment.objects.create(
            risk_score=risk_score,
            assignment=assignment_text
        )
        return Response({
            'risk_score': risk_level,
            'training_assignment': assignment_text
        }, status=status.HTTP_200_OK)

class StartSessionView(APIView):
    """
    POST: /api/start_session/
    Receives user demographics, session duration, and device_id, creates a session, returns session ID.
    """
    def post(self, request, format=None):
        print("Received data:", request.data)
        user_data = request.data.get('user')
        duration = request.data.get('duration')
        device_id = request.data.get('device_id')
        if not user_data or not duration or not device_id:
            return Response({'error': 'user, duration, and device_id are required.'}, status=status.HTTP_400_BAD_REQUEST)
        user_serializer = UserProfileSerializer(data=user_data)
        if user_serializer.is_valid():
            user = user_serializer.save()
        else:
            return Response(user_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        # Deactivate any previous sessions for this device
        Session.objects.filter(device_id=device_id, is_active=True).update(is_active=False)
        session = Session.objects.create(user=user, duration=duration, status='pending', device_id=device_id, is_active=True)
        return Response({'session_id': session.id}, status=status.HTTP_201_CREATED)

class SessionEMGDataView(APIView):
    """
    POST: /api/session_data/
    Receives EMG data for a device (device_id, emg_data). Appends to the active session for that device.
    """
    def post(self, request, format=None):
        device_id = request.data.get('device_id')
        emg_data = request.data.get('emg_data')
        if not device_id or not emg_data:
            return Response({'error': 'device_id and emg_data are required.'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            session = Session.objects.filter(device_id=device_id, is_active=True, status__in=['pending', 'collecting']).latest('created_at')
        except Session.DoesNotExist:
            return Response({'error': 'No active session for this device.'}, status=status.HTTP_404_NOT_FOUND)
        session.status = 'collecting'
        session.started_at = session.started_at or timezone.now()
        session.save()
        EMGData.objects.create(user=session.user, session=session, raw_data=emg_data)
        return Response({'message': 'EMG data received.'}, status=status.HTTP_201_CREATED)

class EndSessionView(APIView):
    """
    POST: /api/end_session/
    Ends the session, processes EMG data, extracts features, predicts risk, and returns result.
    """
    def post(self, request, format=None):
        session_id = request.data.get('session_id')
        fs = request.data.get('fs', 1000)
        if not session_id:
            return Response({'error': 'session_id is required.'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            session = Session.objects.get(id=session_id)
        except Session.DoesNotExist:
            return Response({'error': 'Session not found.'}, status=status.HTTP_404_NOT_FOUND)
        if session.status not in ['collecting', 'pending']:
            return Response({'error': 'Session is not in a state to end.'}, status=status.HTTP_400_BAD_REQUEST)
        session.status = 'processing'
        session.ended_at = timezone.now()
        session.save()
        # Gather all EMG data for this session
        emg_records = session.emg_data.all().order_by('timestamp')
        all_emg = []
        for record in emg_records:
            all_emg.extend(record.raw_data)
        if not all_emg:
            session.status = 'failed'
            session.save()
            return Response({'error': 'No EMG data for session.'}, status=status.HTTP_400_BAD_REQUEST)
        # Extract features
        raw_signal = np.array(all_emg)
        features = extract_features(raw_signal, fs)
        features = convert_numpy_types(features)
        feature_set = FeatureSet.objects.create(emg_data=emg_records.first(), features=features)
        # Prepare user inputs (add BMI if possible)
        user = session.user
        user_inputs = {
            'age': user.age,
            'height': user.height,
            'weight': user.weight,
            'training_frequency': user.training_frequency,
            'previous_injury': user.previous_injury,
            'muscle_group': user.muscle_group,
            'contraction_type': user.contraction_type,
        }
        user_inputs['bmi'] = user.weight / ((user.height / 100) ** 2) if user.height and user.weight else 0
        muscle_group = user.muscle_group
        predictor = InjuryRiskPredictor()
        X_pred = predictor.prepare_features_for_prediction(user_inputs, features, muscle_group)
        model = predictor.models[muscle_group]
        expected_features = list(getattr(model, "feature_names_in_", []))
        if expected_features:
            for col in expected_features:
                if col not in X_pred.columns:
                    X_pred[col] = 0
            X_pred = X_pred[expected_features]
        risk_level = model.predict(X_pred)[0]
        risk_level = str(risk_level)  # Ensure serializable
        risk_score = RiskScore.objects.create(
            feature_set=feature_set,
            score=0,
            level=risk_level
        )
        assignment_text = get_training_assignment(risk_level)
        TrainingAssignment.objects.create(
            risk_score=risk_score,
            assignment=assignment_text
        )
        session.status = 'completed'
        session.save()
        return Response({
            'risk_score': risk_level,
            'training_assignment': assignment_text
        }, status=status.HTTP_200_OK)

class SessionStatusView(APIView):
    """
    GET: /api/session_status/?session_id=...
    Returns the status and result (if available) for a session.
    """
    def get(self, request, format=None):
        session_id = request.GET.get('session_id')
        if not session_id:
            return Response({'error': 'session_id is required.'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            session = Session.objects.get(id=session_id)
        except Session.DoesNotExist:
            return Response({'error': 'Session not found.'}, status=status.HTTP_404_NOT_FOUND)
        data = SessionSerializer(session).data
        # Try to get result
        result = None
        if session.status == 'completed':
            emg_records = session.emg_data.all().order_by('timestamp')
            feature_set = emg_records.first().feature_sets.order_by('-timestamp').first() if emg_records.exists() else None
            risk_score = feature_set.risk_scores.order_by('-timestamp').first() if feature_set else None
            training_assignment = risk_score.training_assignments.order_by('-timestamp').first() if risk_score else None
            result = {
                'risk_score': str(risk_score.level) if risk_score else None,
                'training_assignment': training_assignment.assignment if training_assignment else None
            }
        return Response({'status': session.status, 'result': result, 'session': data}, status=status.HTTP_200_OK)

def convert_numpy_types(obj):
    if isinstance(obj, dict):
        return {k: convert_numpy_types(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy_types(v) for v in obj]
    elif hasattr(obj, 'item'):
        return obj.item()
    else:
        return obj
