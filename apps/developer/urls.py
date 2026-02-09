from django.urls import path
from .views import (
    DevSessionListCreateView, 
    DevSessionDetailView, 
    DevRunStreamView
)

app_name = 'developer'

urlpatterns = [
    # 1. List all sessions or create a new one
    # ENDPOINT: /developer/sessions/
    path('sessions/', DevSessionListCreateView.as_view(), name='session-list-create'),

    # 2. Get details or Delete a specific session
    # ENDPOINT: /developer/sessions/<int:session_id>/
    path('sessions/<int:session_id>/', DevSessionDetailView.as_view(), name='session-detail'),

    # 3. Trigger the AI Coder/Explainer stream
    # URL: /developer/sessions/<session_id>/run/
    path('sessions/<int:session_id>/run/', DevRunStreamView.as_view(), name='session-run-stream'),
]