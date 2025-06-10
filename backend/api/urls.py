from django.urls import path
from .views import StartSessionView, EndSessionView, SessionStatusView

urlpatterns = [
    path('start_session/', StartSessionView.as_view(), name='start_session'),
    path('end_session/', EndSessionView.as_view(), name='end_session'),
    path('session_status/', SessionStatusView.as_view(), name='session_status'),
]