import logging
from django.http import StreamingHttpResponse
from rest_framework.views import APIView
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.db.models import Prefetch
from rest_framework.permissions import IsAuthenticated

from apps.ai_models.models import AiModel
from apps.developer.utils import (
    generate_dev_mode_stream, generate_explainer_only_stream, 
    get_session_history
)
from .models import (
    DevRun, 
    DevSession,
    RunResultStatus
)
from .serializers import (
    AiModelOutSerializer,
    DevSessionOutSerializer, 
    DevSessionDetailOutSerializer, 
    DevSessionCreateAllInSerializer,
)
from core.responses import (
    success_response,
    error_response
)

logger = logging.getLogger(__name__)

# -------------- VIEWS ---------------

# ------- View 1: Dev session (Create and list)
class DevSessionListCreateView(APIView):
    """
    Endpoint 1: List all sessions (for sidebar)
    Endpoint 2: Create Session + Configs (Wizard)
    """
    permission_classes = [IsAuthenticated]
    
    # List all sessions
    def get(self, request):
        sessions = DevSession.objects.filter(user=request.user, is_archived=False)
        # Fetch models right here
        available_models = AiModel.objects.filter(is_active=True)
            
        return success_response(data={
            "sessions": DevSessionOutSerializer(sessions, many=True).data,
            "available_models": AiModelOutSerializer(available_models, many=True).data
        })
        
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
    Endpoint 3: Show session details (Coder/Explainer models configs) and handle delete
    """
    permission_classes = [IsAuthenticated]
    def get(self, request, session_id):
        # Prefetch all teh required models at once rather than hitting the DB many times for the same requets
        session = get_object_or_404(DevSession.objects.prefetch_related('model_configs__ai_model', 
                Prefetch(
                    'runs', 
                    queryset=DevRun.objects.order_by('-created_at') 
                ),
                'runs__results__session_model_config' 
            ),
            id=session_id,
            user=request.user
        )
        serializer = DevSessionDetailOutSerializer(session)
        return success_response(data=serializer.data)

    def delete(self, request, session_id):
        try:
            # 1. Fetch the session
            session = get_object_or_404(DevSession, id=session_id, user=request.user)
            
            # 2. Hard Delete
            # Because of on_delete=models.CASCADE in DevSessionModelConfig,
            # this single line deletes the session AND all associated configs.
            session.delete()
            
            return success_response(message="Session and associated configurations deleted successfully.")

        except Exception as e:
            logger.error(f"Delete Error: {str(e)}")
            return error_response(message="An error occurred while deleting the session.")

# ----------- View 3: Handle requests to the LLMs (click the run or send in the chat)
class DevRunStreamView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request, session_id):

        try:
            # --- 1. Validation and Setup ---
            session = get_object_or_404(DevSession, id=session_id, user=request.user)
            user_prompt = request.data.get("prompt")
            initiator_role = request.data.get("initiator_role")  # "coder" | "explainer"
            target = request.query_params.get('target', 'pipeline')

            if not user_prompt:
                return error_response(message="Prompt is required")
            
            if initiator_role not in ["coder", "explainer"]:
                return error_response(message="initiator_role must be coder or explainer")

            # --- 2. Database Record Creation ---
            #  create this first so there is a record of the attempt
            run_instance = DevRun.objects.create(
                session=session,
                user_prompt=user_prompt,
                initiator_role=initiator_role,
            )

            # --- 3. Memory Retrieval ---
            # Fetches previous messages to give context to the AI
            history = get_session_history(run_instance)

            # --- 4. Logic Branching ---
            if target == 'explainer':
                stream = generate_explainer_only_stream(session, user_prompt, history, run_instance)
            else:
                stream = generate_dev_mode_stream(session, user_prompt, history, run_instance)

            # --- 5. Return the Stream ---
            response = StreamingHttpResponse(stream, content_type='application/json')
            response['X-Accel-Buffering'] = 'no'
            return response

        except Exception as e:
            # Log the technical error for your own debugging
            logger.error(f"Error in DevRunStreamView: {str(e)}")
            
            # If the run_instance was created before the crash, mark it as failed
            if 'run_instance' in locals():
                run_instance.status = RunResultStatus.ERROR
                run_instance.save()
            
            # Return a clean error message to the website user
            return error_response(message="Failed to initialize the AI stream. Please try again.")

