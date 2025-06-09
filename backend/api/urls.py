from django.urls import path
from .views import UserAndEMGDataUploadView, FeatureExtractionView, PredictionAndTrainingView, UserRiskScoreListView, RealTimeSessionView, StartSessionView, SessionEMGDataView, EndSessionView, SessionStatusView

urlpatterns = [
    path('upload/', UserAndEMGDataUploadView.as_view(), name='user_emg_upload'),
    path('extract_features/', FeatureExtractionView.as_view(), name='extract_features'),
    path('predict_and_assign/', PredictionAndTrainingView.as_view(), name='predict_and_assign'),
    path('user_risk_scores/', UserRiskScoreListView.as_view(), name='user_risk_scores'),
    path('submit_session/', RealTimeSessionView.as_view(), name='submit_session'),
    path('start_session/', StartSessionView.as_view(), name='start_session'),
    path('session_data/', SessionEMGDataView.as_view(), name='session_data'),
    path('end_session/', EndSessionView.as_view(), name='end_session'),
    path('session_status/', SessionStatusView.as_view(), name='session_status'),
] 