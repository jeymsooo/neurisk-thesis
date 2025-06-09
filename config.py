# Configuration settings for the muscle injury risk prediction project

import os

# Directory paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, '../data')
RAW_DATA_DIR = os.path.join(DATA_DIR, 'raw')
PROCESSED_DATA_DIR = os.path.join(DATA_DIR, 'processed')

# Model parameters
MODEL_SAVE_PATH = os.path.abspath(os.path.join(BASE_DIR, 'models'))
MODEL_TYPE = 'GradientBoosting'
CROSS_VALIDATION_FOLDS = 5

# EMG feature extraction parameters
FILTER_LOW_CUTOFF = 20  # Low cutoff frequency for bandpass filter
FILTER_HIGH_CUTOFF = 450  # High cutoff frequency for bandpass filter
NOTCH_FREQ = 60  # Frequency to be removed by notch filter

# Synthetic data generation parameters
SYNTHETIC_DATA_SIZE = 1000  # Number of synthetic samples to generate
NOISE_LEVEL = 0.05  # Noise level for synthetic EMG signals

# Prediction thresholds
INJURY_RISK_THRESHOLD = 0.5  # Threshold for predicting high injury risk

# Logging settings
LOGGING_LEVEL = 'INFO'  # Logging level for the application

MODEL_PATHS = {
    'calves': os.path.join(MODEL_SAVE_PATH, 'model_calves.pkl'),
    'hamstrings': os.path.join(MODEL_SAVE_PATH, 'model_hamstrings.pkl'),
    'quadriceps': os.path.join(MODEL_SAVE_PATH, 'model_quadriceps.pkl'),
}