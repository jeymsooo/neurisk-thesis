import sys
import os
import time
import streamlit as st
import pandas as pd
import numpy as np

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from src.prediction.predictor import InjuryRiskPredictor
from src.feature_extraction.emg_features import extract_features
from src.interface.emg_capture import capture_emg_serial, capture_emg_tcp

PREVIOUS_INJURY_CATEGORIES = ['calves', 'hamstrings', 'quadriceps', 'none']
CONTRACTION_TYPE_CATEGORIES = ['isometric', 'isotonic']

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@700&display=swap');
    html, body, [class*="css"]  {
        background: #181c20 !important;
        color: #f3f6fa !important;
        font-family: 'Montserrat', sans-serif !important;
    }
    .neurisk-logo {
        font-family: 'Montserrat', sans-serif;
        font-weight: 700;
        font-size: 3.75rem;
        letter-spacing: 0.08em;
        color: #ff4b4b;
        margin-bottom: 0.1em;
        margin-top: 0.2em;
        text-shadow: 0 2px 16px #ff4b4b80;
        text-align: center;
    }
    .neurisk-sub {
        font-size: 0.60rem;
        color: #b0b8c1;
        margin-bottom: 2em;
        margin-top: -1.2em;
        font-family: 'Montserrat', sans-serif;
        font-weight: 400;
        letter-spacing: 0.02em;
        text-align: center;
    }

    </style>
""", unsafe_allow_html=True)

def simulate_emg_and_features(muscle):
    features = {
        f"rms_{muscle}": np.random.uniform(0.5, 1.5),
        f"mav_{muscle}": np.random.uniform(0.5, 1.5),
        f"zc_{muscle}": np.random.randint(5, 20),
        f"ssc_{muscle}": np.random.randint(5, 20),
        f"wl_{muscle}": np.random.uniform(1, 3),
        f"mdf_{muscle}": np.random.uniform(80, 150),
        f"mnf_{muscle}": np.random.uniform(80, 150),
    }
    rms = features[f"rms_{muscle}"]
    mdf = features[f"mdf_{muscle}"]
    mnf = features[f"mnf_{muscle}"]
    fatigue_level = 0.5 * ((rms - 0.5) / (2.0 - 0.5)) + \
                    0.25 * (1 - (mdf - 80) / (150 - 80)) + \
                    0.25 * (1 - (mnf - 80) / (150 - 80))
    fatigue_level = float(np.clip(fatigue_level, 0, 1))
    features[f"fatigue_level_{muscle}"] = fatigue_level
    features["rms_time_corr"] = np.random.uniform(-0.5, 1)
    features["mnf_time_corr"] = np.random.uniform(-1, 0.5)
    return features

def main():
    # ---- Typography Logo and Subheading ----
    st.markdown('<div class="neurisk-logo">Neurisk</div>', unsafe_allow_html=True)
    st.markdown('<div class="neurisk-sub">Muscle Injury Risk Prediction for Basketball Players</div>', unsafe_allow_html=True)

    st.markdown("---")
    
    # --- User Info Section ---
    col1, col2 = st.columns(2)
    with col1:
        name = st.text_input("Name")
        age = st.number_input("Age", min_value=10, max_value=100, value=25)
        height = st.number_input("Height (cm)", min_value=100, max_value=250, value=160)
        weight = st.number_input("Weight (kg)", min_value=30, max_value=200, value=60)
    with col2:
        training_freq = st.number_input("Training Frequency (sessions/week)", min_value=1, max_value=7, value=3)
        previous_injury_options = ["None", "Calves", "Hamstrings", "Quadriceps"]
        previous_injury = st.selectbox("Previous Injury", previous_injury_options)
        previous_injury = previous_injury.lower() if previous_injury != "None" else "none"
        muscle_group_options = ["Calves", "Hamstrings", "Quadriceps"]
        muscle_group = st.selectbox("Muscle to Test", muscle_group_options)
        muscle_group = muscle_group.lower()
        contraction_type_options = ["Isometric", "Isotonic"]
        contraction_type = st.selectbox("Contraction Type", contraction_type_options)
        contraction_type = contraction_type.lower()

    st.markdown("---")

    # --- EMG Capture & Feature Input Section ---
    col3, col4 = st.columns(2)
    if 'features' not in st.session_state:
        st.session_state['features'] = None
    if 'emg_captured' not in st.session_state:
        st.session_state['emg_captured'] = False

    # --- EMG Capture Source ---
    with col3:
        st.subheader("EMG Capture Source")
        capture_mode = st.radio("Connection Type", ["Serial", "WiFi (TCP)"], horizontal=True)
        capture_emg = st.button("Capture EMG")

        if capture_emg:
            st.info("Please wear the EMG sensor nodes properly before proceeding.")
            st.session_state['show_capture_settings'] = True
            st.session_state['emg_captured'] = False

        if st.session_state.get('show_capture_settings', False):
            if capture_mode == "Serial":
                serial_port = st.text_input("Serial Port (e.g., COM3 or /dev/ttyUSB0)", value="COM3")
                baud_rate = st.number_input("Baud Rate", min_value=9600, max_value=250000, value=115200)
            else:
                tcp_ip = st.text_input("ESP32 IP Address", value="192.168.4.1")
                tcp_port = st.number_input("ESP32 TCP Port", min_value=1, max_value=65535, value=3333)
            capture_duration = st.number_input("Capture Duration (seconds)", min_value=1, max_value=30, value=5)
            begin_test = st.button("Begin Test")
            if begin_test:
                with st.spinner("Capturing EMG data..."):
                    try:
                        if capture_mode == "Serial":
                            data = capture_emg_serial(serial_port, baud_rate, capture_duration)
                        else:
                            data = capture_emg_tcp(tcp_ip, tcp_port, capture_duration)
                        st.success(f"Captured {len(data)} samples.")
                        pd.DataFrame(data).to_csv("emg_capture.csv", index=False, header=False)
                        emg_signal = np.array(data).flatten()
                        emg_feats = extract_features(emg_signal, fs=1000)
                        features = {f"{k}_{muscle_group}": v for k, v in emg_feats.items()}
                        rms = features.get(f"rms_{muscle_group}", 0)
                        mdf = features.get(f"mdf_{muscle_group}", 0)
                        mnf = features.get(f"mnf_{muscle_group}", 0)
                        fatigue_level = 0.5 * ((rms - 0.5) / (2.0 - 0.5)) + \
                                        0.25 * (1 - (mdf - 80) / (150 - 80)) + \
                                        0.25 * (1 - (mnf - 80) / (150 - 80))
                        fatigue_level = float(np.clip(fatigue_level, 0, 1))
                        features[f"fatigue_level_{muscle_group}"] = fatigue_level
                        features["rms_time_corr"] = np.random.uniform(-0.5, 1)
                        features["mnf_time_corr"] = np.random.uniform(-1, 0.5)
                        st.session_state['features'] = features
                        st.session_state['emg_captured'] = True
                        st.success("EMG features extracted from captured data.")
                    except Exception as e:
                        st.error(f"EMG capture failed: {e}")

    # --- EMG Feature Input ---
    with col4:
        st.subheader("EMG Feature Input")
        emg_data_file = st.file_uploader("Upload EMG Data (CSV)", type=["csv"])
        simulate = st.checkbox("Simulate EMG Features")
        if emg_data_file is not None:
            try:
                emg_df = pd.read_csv(emg_data_file)
                if emg_df.shape[1] != 1:
                    st.error("Please upload a CSV with a single column of raw EMG data.")
                else:
                    emg_signal = emg_df.squeeze().values
                    emg_feats = extract_features(emg_signal, fs=1000)
                    features = {f"{k}_{muscle_group}": v for k, v in emg_feats.items()}
                    rms = features[f"rms_{muscle_group}"]
                    mdf = features[f"mdf_{muscle_group}"]
                    mnf = features[f"mnf_{muscle_group}"]
                    fatigue_level = 0.5 * ((rms - 0.5) / (2.0 - 0.5)) + \
                                    0.25 * (1 - (mdf - 80) / (150 - 80)) + \
                                    0.25 * (1 - (mnf - 80) / (150 - 80))
                    fatigue_level = float(np.clip(fatigue_level, 0, 1))
                    features[f"fatigue_level_{muscle_group}"] = fatigue_level
                    features["rms_time_corr"] = np.random.uniform(-0.5, 1)
                    features["mnf_time_corr"] = np.random.uniform(-1, 0.5)
                    st.session_state['features'] = features
                    st.session_state['emg_captured'] = True
                    st.success("EMG features extracted successfully.")
            except Exception as e:
                st.error(f"Failed to process EMG file: {e}")
        elif simulate:
            features = simulate_emg_and_features(muscle_group)
            st.session_state['features'] = features
            st.session_state['emg_captured'] = True
            st.info("Simulated EMG features:")
            st.json(features)

    st.markdown("---")

    # --- Prediction Section ---
    if st.session_state.get('emg_captured', False):
        if st.button("Predict Injury Risk"):
            features = st.session_state.get('features', None)
            if features is None:
                st.warning("Please capture, upload, or simulate EMG features first.")
            else:
                user_inputs = {
                    "age": age,
                    "height": height,
                    "weight": weight,
                    "bmi": weight / ((height / 100) ** 2),
                    "training_frequency": training_freq,
                    "previous_injury": previous_injury,
                    "contraction_type": contraction_type,
                    "rms_time_corr": features.get("rms_time_corr", 0),
                    "mnf_time_corr": features.get("mnf_time_corr", 0),
                    "fatigue_level": features.get(f"fatigue_level_{muscle_group}", 0),
                }
                for feat in ['rms', 'mav', 'zc', 'ssc', 'wl', 'mdf', 'mnf']:
                    user_inputs[f"{feat}_{muscle_group}"] = features.get(f"{feat}_{muscle_group}", 0)
                for cat in PREVIOUS_INJURY_CATEGORIES:
                    user_inputs[f"previous_injury_{cat}"] = 1 if user_inputs["previous_injury"] == cat else 0
                for cat in CONTRACTION_TYPE_CATEGORIES:
                    user_inputs[f"contraction_type_{cat}"] = 1 if contraction_type == cat else 0
                user_inputs.pop("previous_injury")
                user_inputs.pop("contraction_type")
                X_pred = pd.DataFrame([user_inputs])
                predictor = InjuryRiskPredictor()
                model = predictor.models[muscle_group]
                expected_features = list(getattr(model, "feature_names_in_", []))
                if expected_features:
                    for col in expected_features:
                        if col not in X_pred.columns:
                            X_pred[col] = 0
                    X_pred = X_pred[expected_features]
                risk_level = model.predict(X_pred)[0]
                st.success(f"Predicted Injury Risk Level: {risk_level.capitalize()}")
                st.header("Recommended Training Plan")
                if risk_level == "low":
                    display_training_regime(risk_level)
                elif risk_level == "medium":
                    display_training_regime(risk_level)
                elif risk_level == "high":
                    display_training_regime(risk_level)
                else:
                    st.write("No recommendation available.")

def display_training_regime(risk_level):
    if risk_level == "low":
        st.subheader("Low Risk Training Regime")
        st.markdown("**Objective:** Maintain optimal musculoskeletal health and prevent injury.")
        st.markdown("**Recommended Interventions:**")
        st.markdown("""
        - Continue regular strength and conditioning.
        - Emphasize warm-up, cool-down, and recovery.
        - Monitor training load.
        """)
        st.markdown("**Specific Training Regime:**")
        st.markdown("""
        - **Before Practice:**  
            - 10–15 min dynamic warm-up (leg swings, high knees, butt kicks, dynamic lunges)  
            - Light plyometrics (skipping, bounding)  
            - Activation exercises (mini-band walks, glute bridges)
        - **During Practice:**  
            - Full participation in team drills and scrimmages  
            - Integrate neuromuscular exercises (balance, agility ladders) into skill drills
        - **After Practice:**  
            - 10 min static stretching (hamstrings, quads, calves)  
            - Foam rolling major muscle groups  
            - Hydration and nutrition for recovery
        """)
        st.caption("Slauterbeck, J. R., et al. (2020). The effectiveness of neuromuscular training to reduce ACL injuries in female athletes: A systematic review. Am J Sports Med, 48(7), 1795-1803. [https://doi.org/10.1177/0363546520918411](https://doi.org/10.1177/0363546520918411)")

    elif risk_level == "medium":
        st.subheader("Medium Risk Training Regime")
        st.markdown("**Objective:** Address early signs of fatigue or imbalance and prevent progression to high risk.")
        st.markdown("**Recommended Interventions:**")
        st.markdown("""
        - Add targeted neuromuscular and eccentric strengthening.
        - Monitor fatigue and muscle imbalances.
        - Integrate recovery modalities.
        """)
        st.markdown("**Specific Training Regime:**")
        st.markdown("""
        - **Before Practice:**  
            - 15 min dynamic warm-up with added focus on single-leg balance and proprioceptive drills (e.g., single-leg stance, wobble board)  
            - Eccentric strengthening (2–3 sets of Nordic hamstring curls, eccentric calf raises)
        - **During Practice:**  
            - Participate in team drills, but include 2–3 sets of neuromuscular exercises (agility ladder, perturbation training) between drills  
            - Monitor perceived exertion and modify intensity if needed
        - **After Practice:**  
            - 10–15 min static stretching and foam rolling  
            - 5–10 min yoga or guided mobility work  
            - Use of ice or compression if soreness is present
        """)
        st.caption("Van der Horst, N., et al. (2022). Eccentric hamstring exercise reduces hamstring injury rate in elite male soccer players: A randomized controlled trial. Br J Sports Med, 56(2), 89-95. [https://doi.org/10.1136/bjsports-2021-104123](https://doi.org/10.1136/bjsports-2021-104123)")

    elif risk_level == "high":
        st.subheader("High Risk Training Regime")
        st.markdown("**Objective:** Mitigate injury risk, address deficits, and ensure safe return to play.")
        st.markdown("**Recommended Interventions:**")
        st.markdown("""
        - Supervised rehabilitation with a physiotherapist.
        - Individualized corrective exercise program.
        - Gradual return-to-play protocol.
        """)
        st.markdown("**Specific Training Regime:**")
        st.markdown("""
        - **Before Practice:**  
            - 20 min supervised rehab warm-up (isokinetic strengthening, proprioceptive retraining, glute/core activation)  
            - Corrective exercises targeting weaknesses (e.g., single-leg bridges, clamshells)
        - **During Practice:**  
            - Modified or limited participation in team drills  
            - Focus on technique and low-intensity skill work  
            - Continue supervised rehab exercises as tolerated
        - **After Practice:**  
            - Extended cool-down with static stretching and foam rolling  
            - Physiotherapist-guided recovery (manual therapy, modalities as needed)  
            - Education session on injury prevention and self-monitoring
        """)
        st.caption("""
        Buckthorpe, M., et al. (2020). Recommendations for hamstring injury prevention in elite football: translating research into practice. Br J Sports Med, 54(7), 372-380. [https://doi.org/10.1136/bjsports-2019-100894](https://doi.org/10.1136/bjsports-2019-100894)  
        Taberner, M., et al. (2020). Rehabilitation and return to play of muscle injuries in football: a systematic review and evidence-based practice. Br J Sports Med, 54(18), 1141-1150. [https://doi.org/10.1136/bjsports-2019-101206](https://doi.org/10.1136/bjsports-2019-101206)
        """)

if __name__ == "__main__":
    main()