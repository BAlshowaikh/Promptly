from django.http import StreamingHttpResponse
from rest_framework.views import APIView
from rest_framework import status
from django.shortcuts import get_object_or_404

from apps.developer.utils import (
    generate_dev_mode_stream, generate_explainer_only_stream, 
    get_session_history
)
from .models import (
    DevRun, 
    DevSession
)
from .serializers import (
    DevSessionOutSerializer, 
    DevSessionDetailOutSerializer, 
    DevSessionCreateAllInSerializer,
)
from core.responses import (
    success_response,
    error_response
)

# -------------- VIEWS ---------------

# ------- View 1: Dev session (Create and list)
class DevSessionListCreateView(APIView):
    """
    Endpoint 1: List all sessions (for sidebar)
    Endpoint 2: Create Session + Configs (Wizard)
    """
    
    # List all sessions
    def get(self, request):
        sessions = DevSession.objects.filter(user=request.user, is_archived=False)
        serializer = DevSessionOutSerializer(sessions, many=True)
        return success_response(
            data = serializer.data,
            message = "Sessions retrieved successfully"
        )
        
    def post(self, request):
        serializer = DevSessionCreateAllInSerializer(data=request.data)
        
        # Validate the data
        if serializer.is_valid():
            # Pass the logged in user to the serializer 
            session = serializer.save(user=request.user)
            out_serializer = DevSessionDetailOutSerializer(session)
            return success_response(
                data = out_serializer.data,
                message="Session created successfully", 
                status_code=status.HTTP_201_CREATED
            )
        
        # If not valid via the serializer then show the error
        return error_response(message="Validation failed", errors=serializer.errors)
    
# --------------- View 2: Show the session details and session configuration (models) details
class DevSessionDetailView(APIView):
    """
    Endpoint 3: Show session details (Coder/Explainer models configs)
    """
    def get(self, request, session_id):
        session = get_object_or_404(DevSession, id=session_id, user=request.user)
        serializer = DevSessionDetailOutSerializer(session)
        return success_response(data=serializer.data)

# ----------- View 3: Handle requests to the LLMs (click the run or send in the chat)
class DevRunStreamView(APIView):
    def post(self, request, session_id):
        session = get_object_or_404(DevSession, id=session_id, user=request.user)
        user_prompt = request.data.get("prompt")
        target = request.query_params.get('target', 'pipeline')

        if not user_prompt:
            return error_response(message="Prompt is required")

        # 1. Create Run instance
        run_instance = DevRun.objects.create(
            session=session,
            user_prompt=user_prompt
        )

        # 2. Get history
        history = get_session_history(run_instance)

        # 3. Stream Selection
        if target == 'explainer':
            # This triggers ONLY the explainer phase
            stream = generate_explainer_only_stream(session, user_prompt, history, run_instance)
        else:
            # This triggers Coder then Explainer (standard Pipeline)
            stream = generate_dev_mode_stream(session, user_prompt, history, run_instance)

        #StreamingHttpResponse returns chunks directly, 
        response = StreamingHttpResponse(stream, content_type='application/json')
        response['X-Accel-Buffering'] = 'no'
        return response
    
