from django.urls import path
from .views import StartSessionView, EndSessionView, SessionStatusView, UploadEMGView, latest_session_id

urlpatterns = [
    path('start_session/', StartSessionView.as_view(), name='start_session'),
    path('end_session/', EndSessionView.as_view(), name='end_session'),
    path('session_status/', SessionStatusView.as_view(), name='session_status'),
    path('upload_emg/', UploadEMGView.as_view()),
    path('latest_session_id/', latest_session_id, name='latest_session_id'),
]