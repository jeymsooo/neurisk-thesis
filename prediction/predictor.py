import joblib
import numpy as np
import pandas as pd
from feature_extraction.emg_features import extract_features
from config import MODEL_PATHS

# Keep your demographic columns list consistent with training
DEMOGRAPHIC_COLS = [
    'age', 'height', 'weight', 'bmi', 'training_frequency', 'fatigue_level'
]

# Categorical features categories (use all categories seen in training)
PREVIOUS_INJURY_CATEGORIES = ['calves', 'hamstrings', 'quadriceps', 'none']
CONTRACTION_TYPE_CATEGORIES = ['isometric', 'concentric', 'eccentric']

class InjuryRiskPredictor:
    def __init__(self):
        self.models = {
            'calves': joblib.load(MODEL_PATHS['calves']),
            'hamstrings': joblib.load(MODEL_PATHS['hamstrings']),
            'quadriceps': joblib.load(MODEL_PATHS['quadriceps'])
        }

    def prepare_features_for_prediction(self, user_inputs, emg_features, muscle):
        base_features = {}
        for col in DEMOGRAPHIC_COLS:
            base_features[col] = user_inputs.get(col, 0)
        for feat_name, feat_val in emg_features.items():
            base_features[f"{feat_name}_{muscle}"] = feat_val
        prev_injury_val = user_inputs.get('previous_injury', 'none')
        for cat in PREVIOUS_INJURY_CATEGORIES:
            base_features[f"previous_injury_{cat}"] = 1 if prev_injury_val == cat else 0
        contraction_val = user_inputs.get('contraction_type', 'isometric')
        for cat in CONTRACTION_TYPE_CATEGORIES:
            base_features[f"contraction_type_{cat}"] = 1 if contraction_val == cat else 0
        return pd.DataFrame([base_features])

    def predict(self, user_inputs, raw_emg_signal, muscle_group):
        features = extract_features(raw_emg_signal, fs=1000)
        X_pred = self.prepare_features_for_prediction(user_inputs, features, muscle_group)
        model = self.models[muscle_group]
        # Align features with model
        expected_features = list(getattr(model, "feature_names_in_", []))
        if expected_features:
            # Add missing columns with 0
            for col in expected_features:
                if col not in X_pred.columns:
                    X_pred[col] = 0
            # Remove unexpected columns
            X_pred = X_pred[expected_features]
        prediction = model.predict(X_pred)
        return prediction[0]

def predict_injury_risk(user_inputs, raw_emg_signal, muscle_group):
    predictor = InjuryRiskPredictor()
    return predictor.predict(user_inputs, raw_emg_signal, muscle_group)
