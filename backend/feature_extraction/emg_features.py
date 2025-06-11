import numpy as np
from scipy.signal import butter, lfilter

def butter_bandpass(lowcut, highcut, fs, order=5):
    nyq = 0.5 * fs
    low = lowcut / nyq
    high = highcut / nyq
    b, a = butter(order, [low, high], btype='band')
    return b, a

def bandpass_filter(data, lowcut, highcut, fs, order=5):
    b, a = butter_bandpass(lowcut, highcut, fs, order=order)
    y = lfilter(b, a, data)
    return y

def notch_filter(data, freq, fs, quality_factor=30):
    nyq = 0.5 * fs
    low = freq / nyq
    high = low
    b, a = butter(2, [low - (1 / (quality_factor * nyq)), high + (1 / (quality_factor * nyq))], btype='bandstop')
    return lfilter(b, a, data)

def compute_rms(data):
    return np.sqrt(np.mean(data**2))

def compute_mav(data):
    return np.mean(np.abs(data))

def compute_zero_crossings(data):
    return np.sum(np.diff(np.sign(data)) != 0)

def compute_slope_sign_changes(data):
    return np.sum(np.diff(np.sign(np.diff(data))) != 0)

def compute_waveform_length(data):
    return np.sum(np.abs(np.diff(data)))

def extract_features(emg_signal, fs):
    filtered_signal = bandpass_filter(emg_signal, 20, 450, fs)
    filtered_signal = notch_filter(filtered_signal, 50, fs)

    features = {
        'RMS': compute_rms(filtered_signal),
        'MAV': compute_mav(filtered_signal),
        'ZC': compute_zero_crossings(filtered_signal),
        'SSC': compute_slope_sign_changes(filtered_signal),
        'WL': compute_waveform_length(filtered_signal)
    }
    
    return features

# Optional STFT functions can be added here for IMDF and IMNF calculations.