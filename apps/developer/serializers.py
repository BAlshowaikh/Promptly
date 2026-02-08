from rest_framework import serializers
from ai_models.models import AiModel
from .models import (
    DevSession, 
    DevSessionModelConfig, 
    DevRun, 
    RunResultStatus, 
    SessionRole, 
    RunMode
)

# ---------- Serializer 1: To show the list of the avaiable AI models
class AiModelOutSerializer(serializers.ModelSerializer):
    """
    Public-facing data for available AI models (Llama, GPT-4, etc.)
    """
    class Meta:
        model = AiModel
        fields = ['id', 'provider', 'model_name']
        

# -------------- Serializer 2: Handles the listing/adding and updating for the llms setting in each session
class DevSessionModelConfigSerializer(serializers.ModelSerializer):
    """
    Handles both Input (creating/updating) and Output (viewing) 
    for Coder and Explainer settings per session.
    """
    # For Output: Show the details of the linked AI model
    ai_model_details = AiModelOutSerializer(source='ai_model', read_only=True)
    
    class Meta:
        model = DevSessionModelConfig
        fields = [
            'id', 'ai_model', 'ai_model_details', 
            'role', 'temperature', 'system_prompt', 'is_enabled'
        ]
        # ai_model is used for input (ID), ai_model_details for output (JSON)
        extra_kwargs = {'ai_model': {'write_only': True}}
        
# ------- Serializer 3: Listing for user sessions (chats)
class DevSessionOutSerializer(serializers.ModelSerializer):
    """
    Represents the public-facing data for a developer session.
    Used for listing sessions in a sidebar or dashboard.
    """
    class Meta:
        model = DevSession
        fields = [
            'id',
            'title',
            'run_mode',
            'is_archived',
            'last_activity_at'
        ]

# ------- Serializer 4: Deatailed serializer for user session
class DevSessionDetailOutSerializer(serializers.ModelSerializer):
    """
    Comprehensive data for a single Session, including its
    Coder and Explainer configurations.
    """
    # This will retrun two objects one for the coder and the other for explainer
    model_configs = DevSessionModelConfigSerializer(many=True, read_only=True)
    
    class Meta:
        model = DevSession
        fields = [
            'id', 
            'title', 
            'run_mode', 
            'is_archived', 
            'last_activity_at', 
            'model_configs'
        ]

# ---------- Serializer 5: Handles the creation of 
class DevSessionCreateInSerializer(serializers.ModelSerializer):
    """
    Handles the creation of a new session. 
    """
    class Meta:
        model = DevSession
        fields = ['title', 'run_mode']